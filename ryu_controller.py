# ryu_controller.py
# FINAL COMPLETE CONTROLLER CODE
from ryu.base import app_manager
from ryu.controller import ofp_event
from ryu.controller.handler import CONFIG_DISPATCHER, MAIN_DISPATCHER, set_ev_cls
from ryu.ofproto import ofproto_v1_3
from ryu.lib.packet import packet, ethernet, ether_types
import threading
import time
import os

# Import the Database Manager (Tested & Verified)
# from database.db_manager import safe_write  # TODO: Re-enable when Module 2 (forensic) is wired in

# =====================================================================
# ⚠️ MODULE IMPORTS (COMMENTED OUT FOR TOPOLOGY TESTING)
# Uncomment these later when we create the module files
# =====================================================================
# from modules.module1_detect import DetectionModule
# from modules.module2_forensic import ForensicModule
# from modules.module3_contain import ContainmentModule
# from modules.module4_rollback import RollbackModule
# from modules.module5_backup import BackupModule  # Pending Supervisor

class IoMTController(app_manager.RyuApp):
    # CRITICAL: Must match topology.py OpenFlow 1.3
    OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]

    def __init__(self, *args, **kwargs):
        super(IoMTController, self).__init__(*args, **kwargs)
        
        # 1. State Tracking
        self.mac_to_port = {}
        self.datapaths = {}           # Stores our 3 switches (s1, s2, s3)
        self.fast_mode = False        # Adaptive Two-Tier Polling flag
        
        # 2. Concurrency Control (Race Condition Prevention)
        self.forensic_complete = threading.Event() 
        
        # =====================================================================
        # ⚠️ MODULE INITIALIZATION (COMMENTED OUT FOR TOPOLOGY TESTING)
        # =====================================================================
        # print("[*] Initializing IoMT Security Modules...")
        # self.detect_module = DetectionModule(self)
        # self.forensic_module = ForensicModule(self)
        # self.contain_module = ContainmentModule(self)
        # self.rollback_module = RollbackModule(self)
        # self.backup_module = BackupModule(self) # Pending Supervisor
        
        # =====================================================================
        # ⚠️ ADAPTIVE POLLING THREAD (COMMENTED OUT FOR TOPOLOGY TESTING)
        # Polling is not needed just to test pingall
        # =====================================================================
        # self.monitor_thread = threading.Thread(target=self._poll_flow_stats, daemon=True)
        # self.monitor_thread.start()
        
        print("\n[*] Ryu Controller Ready.")
        print("[*] Topology Test Mode ACTIVE (Security Modules Disabled)")
        print("[*] Waiting for switches to connect...")

    # =========================================================================
    # SWITCH CONNECTION & BASELINE RULES (L2 Switching - ACTIVE FOR TESTING)
    # =========================================================================

    @set_ev_cls(ofp_event.EventOFPSwitchFeatures, CONFIG_DISPATCHER)
    def switch_features_handler(self, ev):
        """Called when s1, s2, or s3 connects to Ryu."""
        datapath = ev.msg.datapath
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser
        
        # Register the switch
        self.datapaths[datapath.id] = datapath
        print(f"[+] Switch Connected: Datapath ID {datapath.id}")

        # Install Table-Miss flow (Send unknown packets to Ryu)
        match = parser.OFPMatch()
        actions = [parser.OFPActionOutput(ofproto.OFPP_CONTROLLER, ofproto.OFPCML_NO_BUFFER)]
        self.add_flow(datapath, 0, match, actions)

    def add_flow(self, datapath, priority, match, actions, buffer_id=None):
        """Helper to install flow rules on the switches."""
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser
        inst = [parser.OFPInstructionActions(ofproto.OFPIT_APPLY_ACTIONS, actions)]
        if buffer_id:
            mod = parser.OFPFlowMod(datapath=datapath, buffer_id=buffer_id, priority=priority, match=match, instructions=inst)
        else:
            mod = parser.OFPFlowMod(datapath=datapath, priority=priority, match=match, instructions=inst)
        datapath.send_msg(mod)

    @set_ev_cls(ofp_event.EventOFPPacketIn, MAIN_DISPATCHER)
    def _packet_in_handler(self, ev):
        """Handles basic L2 switching so hospital devices can communicate."""
        msg = ev.msg
        datapath = msg.datapath
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser
        in_port = msg.match['in_port']

        pkt = packet.Packet(msg.data)
        eth = pkt.get_protocols(ethernet.ethernet)[0]

        if eth.ethertype == ether_types.ETH_TYPE_IPV6:
            return

        dst = eth.dst
        src = eth.src
        dpid = datapath.id

        self.mac_to_port.setdefault(dpid, {})
        self.mac_to_port[dpid][src] = in_port

        if dst in self.mac_to_port[dpid]:
            out_port = self.mac_to_port[dpid][dst]
        else:
            out_port = ofproto.OFPP_FLOOD

        actions = [parser.OFPActionOutput(out_port)]

        if out_port != ofproto.OFPP_FLOOD:
            match = parser.OFPMatch(in_port=in_port, eth_dst=dst, eth_src=src)
            if msg.buffer_id != ofproto.OFP_NO_BUFFER:
                self.add_flow(datapath, 1, match, actions, msg.buffer_id)
                return
            else:
                self.add_flow(datapath, 1, match, actions)

        data = None
        if msg.buffer_id == ofproto.OFP_NO_BUFFER:
            data = msg.data

        out = parser.OFPPacketOut(datapath=datapath, buffer_id=msg.buffer_id, in_port=in_port, actions=actions, data=data)
        datapath.send_msg(out)

    # =========================================================================
    # ADAPTIVE POLLING & FLOW STATISTICS
    # =========================================================================

    def _poll_flow_stats(self):
        """Background thread polling switches based on Fast/Normal mode."""
        NORMAL_INTERVAL = 1.0  # 1 second Heartbeat
        FAST_INTERVAL = 0.1    # 100ms Attack mode
        
        while True:
            # Adaptive two-tier polling interval
            interval = FAST_INTERVAL if self.fast_mode else NORMAL_INTERVAL
            time.sleep(interval)
            
            # Request stats from all connected switches
            for dp in self.datapaths.values():
                self._request_flow_stats(dp)

    def _request_flow_stats(self, datapath):
        """Send OFPFlowStatsRequest to the switch."""
        parser = datapath.ofproto_parser
        req = parser.OFPFlowStatsRequest(datapath)
        datapath.send_msg(req)

    @set_ev_cls(ofp_event.EventOFPFlowStatsReply, MAIN_DISPATCHER)
    def flow_stats_reply_handler(self, ev):
        """
        Receives flow stats from switches and passes them to Module 1.
        """
        body = ev.msg.body
        datapath_id = ev.msg.datapath.id
        
        # =====================================================================
        # ⚠️ MODULE 1 TRIGGER (COMMENTED OUT FOR TOPOLOGY TESTING)
        # =====================================================================
        # self.detect_module.analyze_flow_stats(body, datapath_id)
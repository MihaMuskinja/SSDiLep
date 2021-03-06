#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
algs.py

This module contains a set of analysis specific algs 
for calculating variables, applying selection and 
plotting.
"""

## std modules
import itertools
import os
import math
import ROOT

## logging
import logging
log = logging.getLogger(__name__)

## python
from itertools import combinations
from copy import copy

## pyframe
import pyframe

import mcutils

GeV = 1000.0

#------------------------------------------------------------------------------
class CutAlg(pyframe.core.Algorithm):
    """
    Filtering alg for applying a single cut.  The predefined cuts must be
    implemeneted as a function with the prefix "cut_". One can then specify the
    cut to be applied by passing the cut=<cut name> in the constructor, which
    will execture the cut_<cut name>() function.
    """
    #__________________________________________________________________________
    def __init__(self,
                 name     = None,
                 cut      = None,
                 cutflow  = None,
                 isfilter = True,
                 ):
        pyframe.core.Algorithm.__init__(self, name if name else cut,isfilter=isfilter)
        self.cutflow = cutflow
         
    #__________________________________________________________________________
    def execute(self, weight):
        pyframe.core.Algorithm.execute(self, weight)

        return self.apply_cut(self.name)

    #__________________________________________________________________________
    def apply_cut(self,cutname):
        if self.store.has_key(cutname): return self.store[cutname]
        cut_function = 'cut_%s'%cutname
        assert hasattr(self,cut_function),"cut %s doesnt exist!'"%(cutname)
        self.store[cutname] = result = getattr(self,cut_function)()
        return result
    
    #__________________________________________________________________________
    def cut_AtLeastOneMuon(self):
        return self.chain.nmuon > 0
    
    #__________________________________________________________________________
    def cut_AtLeastTwoMuons(self):
      return self.chain.nmuon > 1
    
    #__________________________________________________________________________
    def cut_OneMuon(self):
        return self.chain.nmuon == 1
    
    #__________________________________________________________________________
    def cut_TwoMuons(self):
        return self.chain.nmuon == 2
    
    #__________________________________________________________________________
    def cut_TwoSSMuons(self):
      muons  = self.store['muons']
      if len(muons)==2:
        if muons[0].trkcharge * muons[1].trkcharge > 0.0:
          return True
      return False
    
    #__________________________________________________________________________
    def cut_TwoOSMuons(self):
      muons  = self.store['muons']
      if len(muons)==2:
        if muons[0].trkcharge * muons[1].trkcharge < 0.0:
          return True
      return False
    
    #__________________________________________________________________________
    def cut_OneJet(self):
        return self.chain.njets == 1
    
    #__________________________________________________________________________
    def cut_AtLeastOneJet(self):
        return self.chain.njets > 0
    
    #__________________________________________________________________________
    def cut_AtLeastTwoJets(self):
        return self.chain.njets > 1
    
    #__________________________________________________________________________
    def cut_AllMuPt22(self):
      muons = self.store['muons']
      passed = True
      for m in muons:
        passed = passed and m.tlv.Pt()>=22.0*GeV
      return passed
    
    #__________________________________________________________________________
    def cut_AllMuEta247(self):
      muons = self.store['muons']
      passed = True
      for m in muons:
        passed = passed and abs(m.tlv.Eta())<2.47
      return passed
    
    #__________________________________________________________________________
    def cut_MuTT(self):
      muons = self.store['muons']
      lead_is_tight = bool(muons[0].isIsolated_FixedCutTightTrackOnly and muons[0].trkd0sig<3.)
      sublead_is_tight = bool(muons[1].isIsolated_FixedCutTightTrackOnly and muons[1].trkd0sig<3.)
      return lead_is_tight and sublead_is_tight
    #__________________________________________________________________________
    def cut_MuTL(self):
      muons = self.store['muons']
      lead_is_tight = bool(muons[0].isIsolated_FixedCutTightTrackOnly and muons[0].trkd0sig<3.)
      sublead_is_loose = bool(not muons[1].isIsolated_FixedCutTightTrackOnly and muons[1].trkd0sig<10.)
      return lead_is_tight and sublead_is_loose
    #__________________________________________________________________________
    def cut_MuLT(self):
      muons = self.store['muons']
      sublead_is_tight = bool(muons[1].isIsolated_FixedCutTightTrackOnly and muons[1].trkd0sig<3.)
      lead_is_loose = bool(not muons[0].isIsolated_FixedCutTightTrackOnly and muons[0].trkd0sig<10.)
      return lead_is_loose and sublead_is_tight
    #__________________________________________________________________________
    def cut_MuLL(self):
      muons = self.store['muons']
      lead_is_loose = bool(not muons[0].isIsolated_FixedCutTightTrackOnly and muons[0].trkd0sig<10.)
      sublead_is_loose = bool(not muons[1].isIsolated_FixedCutTightTrackOnly and muons[1].trkd0sig<10.)
      return lead_is_loose and sublead_is_loose
    
    
    #__________________________________________________________________________
    def cut_LeadMuIsoTight(self):
      muons = self.store['muons']
      lead_mu = muons[0]
      return lead_mu.isIsolated_FixedCutTightTrackOnly
    
    #__________________________________________________________________________
    def cut_SubLeadMuIsoTight(self):
      muons = self.store['muons']
      sublead_mu = muons[1]
      return sublead_mu.isIsolated_FixedCutTightTrackOnly

    #__________________________________________________________________________
    def cut_LeadMuIsoNotTight(self):
      muons = self.store['muons']
      lead_mu = muons[0]
      return not lead_mu.isIsolated_FixedCutTightTrackOnly
    
    #__________________________________________________________________________
    def cut_SubLeadMuIsoNotTight(self):
      muons = self.store['muons']
      sublead_mu = muons[1]
      return not sublead_mu.isIsolated_FixedCutTightTrackOnly

    #__________________________________________________________________________
    def cut_MuPairsIsoTight(self):
      cname = "MuPairsIsoTight"
      pairs = self.store['mu_pairs']
      for p in pairs:
        p.StoreCut(cname,True)
        if self.sampletype == "mc": pass
          #if not p.isTruthMatchedToMuonPair(): continue
        if not (p.lead.isIsolated_FixedCutTightTrackOnly and p.sublead.isIsolated_FixedCutTightTrackOnly): 
          p.StoreCut(cname,False)
      return True
    
    #__________________________________________________________________________
    def cut_MuPairsLeadIsoTightSubLeadIsoNotTight(self):
      cname = "MuPairsLeadIsoTightSubLeadIsoNotTight"
      pairs = self.store['mu_pairs']
      for p in pairs:
        p.StoreCut(cname,True)
        if self.sampletype == "mc": pass
          #if not p.isTruthMatchedToMuonPair(): continue
        if not (p.lead.isIsolated_FixedCutTightTrackOnly and (p.sublead.isIsolated_Loose or p.sublead.isIsolated_FixedCutLoose)): 
          p.StoreCut(cname,False)
      return True
    
    #__________________________________________________________________________
    def cut_MuPairsLeadIsoNotTightSubLeadIsoTight(self):
      cname = "MuPairsLeadIsoNotTightSubLeadIsoTight"
      pairs = self.store['mu_pairs']
      for p in pairs:
        p.StoreCut(cname,True)
        if self.sampletype == "mc": pass
          #if not p.isTruthMatchedToMuonPair(): continue
        if not (p.sublead.isIsolated_FixedCutTightTrackOnly and (p.lead.isIsolated_Loose or p.lead.isIsolated_FixedCutLoose)): 
          p.StoreCut(cname,False)
      return True
    
    #__________________________________________________________________________
    def cut_MuPairsLeadIsoNotTightSubLeadIsoNotTight(self):
      cname = "MuPairsLeadIsoNotTightSubLeadIsoNotTight"
      pairs = self.store['mu_pairs']
      for p in pairs:
        p.StoreCut(cname,True)
        if self.sampletype == "mc": pass
          #if not p.isTruthMatchedToMuonPair(): continue
        if not ((p.sublead.isIsolated_Loose or p.sublead.isIsolated_FixedCutLoose) and (p.lead.isIsolated_Loose or p.lead.isIsolated_FixedCutLoose)): 
          p.StoreCut(cname,False)
      return True

    #__________________________________________________________________________
    def cut_MuPairsLeadPt25SubLeadPt22(self):
      cname = "MuPairsLeadPt25SubLeadPt22"
      pairs = self.store['mu_pairs']
      for p in pairs:
        p.StoreCut(cname,True)
        if p.lead.tlv.Pt()<25*GeV and p.sublead.tlv.Pt()<22*GeV: 
          p.StoreCut(cname,False)
      return True
    
    #__________________________________________________________________________
    def cut_MuPairsLeadPt20SubLeadPt15(self):
      cname = "MuPairsLeadPt20SubLeadPt15"
      pairs = self.store['mu_pairs']
      for p in pairs:
        p.StoreCut(cname,True)
        if p.lead.tlv.Pt()<20*GeV and p.sublead.tlv.Pt()<15*GeV: 
          p.StoreCut(cname,False)
      return True
    
    #__________________________________________________________________________
    def cut_MuPairsLeadPt25SubLeadPt20(self):
      cname = "MuPairsLeadPt25SubLeadPt20"
      pairs = self.store['mu_pairs']
      for p in pairs:
        p.StoreCut(cname,True)
        if p.lead.tlv.Pt()<25*GeV and p.sublead.tlv.Pt()<20*GeV: 
          p.StoreCut(cname,False)
      return True
    
    #__________________________________________________________________________
    def cut_MuPairsMVis15(self):
      cname = "MuPairsMVis15"
      pairs = self.store['mu_pairs']
      for p in pairs:
        p.StoreCut(cname,True)
        if p.m_vis<15*GeV: 
          p.StoreCut(cname,False)
      return True
    
    #__________________________________________________________________________
    def cut_MuPairsMZwindow(self):
      cname = "MuPairsMZwindow"
      mZ = 91.1876*GeV
      pairs = self.store['mu_pairs']
      for p in pairs:
        p.StoreCut(cname,True)
        if abs(p.m_vis - mZ)<10*GeV: 
          p.StoreCut(cname,False)
      return True

    #__________________________________________________________________________
    def cut_MZwindow(self):
      mZ = 91.1876*GeV
      muons = self.store['muons']
      mu_lead = muons[0] 
      mu_sublead = muons[1] 
      m_vis = (mu_lead.tlv + mu_sublead.tlv).M()

      return abs(m_vis - mZ) > 30*GeV
    
    #__________________________________________________________________________
    def cut_M15(self):
      muons = self.store['muons']
      mu_lead = muons[0] 
      mu_sublead = muons[1] 
      m_vis = (mu_lead.tlv + mu_sublead.tlv).M()

      return abs(m_vis)>15*GeV

    #__________________________________________________________________________
    def cut_MuPairsInvMZwindow(self):
      cname = "MuPairsInvMZwindow"
      mZ = 91.1876*GeV
      pairs = self.store['mu_pairs']
      for p in pairs:
        p.StoreCut(cname,True)
        if abs(p.m_vis - mZ)>10*GeV: 
          p.StoreCut(cname,False)
      return True
    
    #__________________________________________________________________________
    def cut_MuPairsAreSS(self):
      cname = "MuPairsAreSS"
      pairs = self.store['mu_pairs']
      for p in pairs:
        p.StoreCut(cname,True)
        if p.charge_product<0.0: 
          p.StoreCut(cname,False)
      return True
    
    #__________________________________________________________________________
    def cut_MuPairsAreOS(self):
      cname = "MuPairsAreOS"
      pairs = self.store['mu_pairs']
      for p in pairs:
        p.StoreCut(cname,True)
        if p.charge_product>0.0: 
          p.StoreCut(cname,False)
      return True
    
    #__________________________________________________________________________
    def cut_MuPairsDeltaRJet04(self):
      cname = "MuPairsDeltaRJet04"
      jets = self.store['jets']
      pairs = self.store['mu_pairs']
      
      for p in pairs:
        p.StoreCut(cname,True)
        for j in jets:
          if j.tlv.DeltaR(p.lead.tlv)<0.4 or j.tlv.DeltaR(p.sublead.tlv)<0.4:
            p.StoreCut(cname,False)
      return True
    
    
    #__________________________________________________________________________
    def cut_MuPairsTT(self):
      cname = "MuPairsTT"
      pairs = self.store['mu_pairs']
      for p in pairs:
        lead_is_tight = bool(p.lead.isIsolated_FixedCutTightTrackOnly and p.lead.trkd0sig<3.)
        sublead_is_tight = bool(p.sublead.isIsolated_FixedCutTightTrackOnly and p.sublead.trkd0sig<3.)
        p.StoreCut(cname,lead_is_tight and sublead_is_tight)
      return True 
    #__________________________________________________________________________
    def cut_MuPairsTL(self):
      cname = "MuPairsTL"
      pairs = self.store['mu_pairs']
      for p in pairs:
        lead_is_tight = bool(p.lead.isIsolated_FixedCutTightTrackOnly and p.lead.trkd0sig<3.)
        sublead_is_loose = bool(not p.sublead.isIsolated_FixedCutTightTrackOnly and p.sublead.trkd0sig<10.)
        p.StoreCut(cname,lead_is_tight and sublead_is_loose)
      return True 
    #__________________________________________________________________________
    def cut_MuPairsLT(self):
      cname = "MuPairsLT"
      pairs = self.store['mu_pairs']
      for p in pairs:
        lead_is_loose = bool(not p.lead.isIsolated_FixedCutTightTrackOnly and p.lead.trkd0sig<10.)
        sublead_is_tight = bool(p.sublead.isIsolated_FixedCutTightTrackOnly and p.sublead.trkd0sig<3.)
        p.StoreCut(cname,lead_is_loose and sublead_is_tight)
      return True 
    #__________________________________________________________________________
    def cut_MuPairsLL(self):
      cname = "MuPairsLL"
      pairs = self.store['mu_pairs']
      for p in pairs:
        lead_is_loose = bool(not p.lead.isIsolated_FixedCutTightTrackOnly and p.lead.trkd0sig<10.)
        sublead_is_loose = bool(not p.sublead.isIsolated_FixedCutTightTrackOnly and p.sublead.trkd0sig<10.)
        p.StoreCut(cname,lead_is_loose and sublead_is_loose)
      return True 
    
    #__________________________________________________________________________
    def cut_MuPairsMatchSingleMuIsoChain(self):
      cname = "MuPairsMatchSingleMuIsoChain"
      pairs = self.store['mu_pairs']
      #trig = {"HLT_mu20_L1MU15":0, "HLT_mu20_iloose_L1MU15":1, "HLT_mu50":2} # for the "ntuples" file
      trig = {"HLT_mu20_L1MU15":0, "HLT_mu20_iloose_L1MU15":0, "HLT_mu50":1}
      
      for p in pairs:
        p.StoreCut(cname,False)
        
        if p.lead.isTrigMatchedToChain.at(trig["HLT_mu20_iloose_L1MU15"]) or p.lead.isTrigMatchedToChain.at(trig["HLT_mu50"]):
          if p.sublead.isTrigMatchedToChain.at(trig["HLT_mu20_iloose_L1MU15"]) or p.sublead.isTrigMatchedToChain.at(trig["HLT_mu50"]): 
            p.StoreCut(cname,True)
        
        #if p.lead.isTrigMatchedToChain.at(trig["HLT_mu20_iloose_L1MU15"]) or p.lead.isTrigMatchedToChain.at(trig["HLT_mu50"]) : p.StoreCut(cname,True)
        #if p.sublead.isTrigMatchedToChain.at(trig["HLT_mu20_iloose_L1MU15"]) or p.sublead.isTrigMatchedToChain.at(trig["HLT_mu50"]) : p.StoreCut(cname,True)
      
      return True

    #__________________________________________________________________________
    def cut_MatchSingleMuIsoChain(self):
      muons = self.store['muons']
      #trig = {"HLT_mu20_L1MU15":0, "HLT_mu20_iloose_L1MU15":1, "HLT_mu50":2} # for the "ntuples" file
      trig = {"HLT_mu20_L1MU15":0, "HLT_mu20_iloose_L1MU15":0, "HLT_mu50":1}
      for m in muons:
        if m.isTrigMatchedToChain.at(trig["HLT_mu20_iloose_L1MU15"]) or m.isTrigMatchedToChain.at(trig["HLT_mu50"]) : return True
      return False
    #__________________________________________________________________________
    def cut_PassSingleMuIsoChain(self):
      chain = ["HLT_mu20_iloose_L1MU15","HLT_mu50"]
      for i in xrange(self.chain.passedTriggers.size()):
        if self.chain.passedTriggers.at(i) in chain: return True
      return False
    
    
    
    #__________________________________________________________________________
    def cut_MatchSingleMuPrescChainLow(self):
      muons = self.store['muons']
      trig = {"HLT_mu20_L1MU15":0,"HLT_mu24":1}
      for m in muons:
        #if m.isTrigMatchedToChain.at(trig["HLT_mu20_L1MU15"]) or m.isTrigMatchedToChain.at(trig["HLT_mu24"]): return True
        if m.isTrigMatchedToChain.at(trig["HLT_mu20_L1MU15"]): return True
      return False
    #__________________________________________________________________________
    def cut_PassSingleMuPrescChainLow(self):
      #chain = ["HLT_mu20_L1MU15","HLT_mu24"]
      chain = ["HLT_mu20_L1MU15"]
      for i in xrange(self.chain.passedTriggers.size()):
        if self.chain.passedTriggers.at(i) in chain: return True
      return False
    
    #__________________________________________________________________________
    def cut_MatchSingleMuPrescChainAll(self):
      muons = self.store['muons']
      trig = {"HLT_mu20_L1MU15":0,"HLT_mu24":1}
      for m in muons:
        if m.isTrigMatchedToChain.at(trig["HLT_mu20_L1MU15"]) or m.isTrigMatchedToChain.at(trig["HLT_mu24"]): return True
      return False
    #__________________________________________________________________________
    def cut_PassSingleMuPrescChainAll(self):
      chain = ["HLT_mu20_L1MU15","HLT_mu24"]
      for i in xrange(self.chain.passedTriggers.size()):
        if self.chain.passedTriggers.at(i) in chain: return True
      return False
    
    
    
    #__________________________________________________________________________
    def cut_PassDiMuChain(self):
      chain = ["HLT_2mu10"]
      for i in xrange(self.chain.passedTriggers.size()):
        if self.chain.passedTriggers.at(i) in chain: return True
      return False
    
    #__________________________________________________________________________
    def cut_LeadMuTruthFilter(self):
      muons = self.store['muons'] 
      if self.sampletype == "mc":
        return muons[0].isTrueIsoMuon()
      return True
    
    #__________________________________________________________________________
    def cut_SubLeadMuTruthFilter(self):
      muons = self.store['muons'] 
      if self.sampletype == "mc":
        return muons[1].isTrueIsoMuon()
      return True
    
    #__________________________________________________________________________
    def cut_MuTruthFilter(self):
      muons = self.store['muons'] 
      if self.sampletype == "mc":
        for m in muons:
          if not m.isTrueIsoMuon(): return False
      return True 
    
    #__________________________________________________________________________
    def cut_MuPairsTruthFilter(self):
      cname = "MuPairsTruthFilter"
      pairs = self.store['mu_pairs']
      for p in pairs:
        p.StoreCut(cname,True)
        if self.sampletype == "mc":
          if not (p.lead.isTrueIsoMuon() and p.sublead.isTrueIsoMuon()):
            p.StoreCut(cname,False)
      return True
   
    #__________________________________________________________________________
    def cut_MuPairsAngleHi10Low25(self):
      cname = "MuPairsAngleHi10Low25"
      pairs = self.store['mu_pairs']
      for p in pairs:
        p.StoreCut(cname,True)
        if p.angle < 1.0 or p.angle > 2.5:
          p.StoreCut(cname,False)
      
      for p in pairs:
        if (p.angle < 1.0 or p.angle > 2.5):
         print p, p.cdict, len(pairs), p.angle
      return True
    
    #__________________________________________________________________________
    def cut_MuPairsZ0SinThetaNot002(self):
      cname = "MuPairsZ0SinThetaNot002"
      pairs = self.store['mu_pairs']
      for p in pairs:
        p.StoreCut(cname,True)
        if not (abs(p.lead.trkz0sintheta)>0.02 and abs(p.sublead.trkz0sintheta)>0.02):
          p.StoreCut(cname,False)
      return True
   
    #__________________________________________________________________________
    def cut_MuPairsFilterTT(self):
      cname = "MuPairsFilterTT"
      pairs = self.store['mu_pairs']
      for p in pairs:
        p.StoreCut(cname,True)
        if self.sampletype == "mc":
          if not (p.lead.isTrueIsoMuon() and p.sublead.isTrueIsoMuon()):
            p.StoreCut(cname,False)
      return True
    #__________________________________________________________________________
    def cut_MuPairsFilterLT(self):
      cname = "MuPairsFilterLT"
      pairs = self.store['mu_pairs']
      for p in pairs:
        p.StoreCut(cname,True)
        if self.sampletype == "mc":
          if not (p.lead.isTrueNonIsoMuon() and p.sublead.isTrueIsoMuon()):
            p.StoreCut(cname,False)
      return True
    #__________________________________________________________________________
    def cut_MuPairsFilterTL(self):
      cname = "MuPairsFilterTL"
      pairs = self.store['mu_pairs']
      for p in pairs:
        p.StoreCut(cname,True)
        if self.sampletype == "mc":
          if not (p.lead.isTrueIsoMuon() and p.sublead.isTrueNonIsoMuon()):
            p.StoreCut(cname,False)
      return True
    #__________________________________________________________________________
    def cut_MuPairsFilterLL(self):
      cname = "MuPairsFilterLL"
      pairs = self.store['mu_pairs']
      for p in pairs:
        p.StoreCut(cname,True)
        if self.sampletype == "mc":
          if not (p.lead.isTrueNonIsoMuon() and p.sublead.isTrueNonIsoMuon()):
            p.StoreCut(cname,False)
      return True
   
   
    #__________________________________________________________________________
    def cut_LeadMuD0Sig2(self):
      muons = self.store['muons']
      return muons[0].trkd0sig<2. 
    #__________________________________________________________________________
    def cut_LeadMuD0Sig3(self):
      muons = self.store['muons']
      return muons[0].trkd0sig<3. 
    #__________________________________________________________________________
    def cut_LeadMuD0Sig4(self):
      muons = self.store['muons']
      return muons[0].trkd0sig<4. 
    #__________________________________________________________________________
    def cut_LeadMuD0Sig5(self):
      muons = self.store['muons']
      return muons[0].trkd0sig<5. 
    #__________________________________________________________________________
    def cut_LeadMuD0Sig6(self):
      muons = self.store['muons']
      return muons[0].trkd0sig<6. 
    #__________________________________________________________________________
    def cut_LeadMuD0Sig10(self):
      muons = self.store['muons']
      return muons[0].trkd0sig<10. 
    
    
    #__________________________________________________________________________
    def cut_LeadMuD0SigNot2(self):
      muons = self.store['muons']
      return muons[0].trkd0sig>2. 
    #__________________________________________________________________________
    def cut_LeadMuD0SigNot3(self):
      muons = self.store['muons']
      return muons[0].trkd0sig>3. 
    #__________________________________________________________________________
    def cut_LeadMuD0SigNot4(self):
      muons = self.store['muons']
      return muons[0].trkd0sig>4. 
    #__________________________________________________________________________
    def cut_LeadMuD0SigNot5(self):
      muons = self.store['muons']
      return muons[0].trkd0sig>5. 
    #__________________________________________________________________________
    def cut_LeadMuD0SigNot6(self):
      muons = self.store['muons']
      return muons[0].trkd0sig>6. 
    #__________________________________________________________________________
    def cut_LeadMuD0SigNot10(self):
      muons = self.store['muons']
      return muons[0].trkd0sig>10. 
    
    
    
    
    
    #__________________________________________________________________________
    def cut_LeadMuZ0SinTheta1(self):
      muons = self.store['muons']
      return abs(muons[0].trkz0sintheta)<1.0
    
    #__________________________________________________________________________
    def cut_LeadMuZ0SinTheta01(self):
      muons = self.store['muons']
      return abs(muons[0].trkz0sintheta)<0.1
    
    #__________________________________________________________________________
    def cut_LeadMuZ0SinTheta005(self):
      muons = self.store['muons']
      return abs(muons[0].trkz0sintheta)<0.05
    
    #__________________________________________________________________________
    def cut_LeadMuZ0SinTheta02(self):
      muons = self.store['muons']
      return abs(muons[0].trkz0sintheta)<0.2
    
    #__________________________________________________________________________
    def cut_LeadMuZ0SinTheta05(self):
      muons = self.store['muons']
      return abs(muons[0].trkz0sintheta)<0.5
    
    
    
    #__________________________________________________________________________
    def cut_LeadMuZ0SinThetaNot1(self):
      muons = self.store['muons']
      return abs(muons[0].trkz0sintheta)>1.0
    
    #__________________________________________________________________________
    def cut_LeadMuZ0SinThetaNot01(self):
      muons = self.store['muons']
      return abs(muons[0].trkz0sintheta)>0.1
    
    #__________________________________________________________________________
    def cut_LeadMuZ0SinThetaNot005(self):
      muons = self.store['muons']
      return abs(muons[0].trkz0sintheta)>0.05
    
    #__________________________________________________________________________
    def cut_LeadMuZ0SinThetaNot02(self):
      muons = self.store['muons']
      return abs(muons[0].trkz0sintheta)>0.2
    
    
    #__________________________________________________________________________
    def cut_OneZ0SinThetaNot002(self):
      muons = self.store['muons']
      return abs(muons[0].trkz0sintheta)>0.02 or abs(muons[1].trkz0sintheta)>0.02
    #__________________________________________________________________________
    def cut_OneZ0SinThetaNot005(self):
      muons = self.store['muons']
      return abs(muons[0].trkz0sintheta)>0.05 or abs(muons[1].trkz0sintheta)>0.05
    #__________________________________________________________________________
    def cut_Z0SinThetaNot002(self):
      muons = self.store['muons']
      return abs(muons[0].trkz0sintheta)>0.02 and abs(muons[1].trkz0sintheta)>0.02
    #__________________________________________________________________________
    def cut_Z0SinThetaNot005(self):
      muons = self.store['muons']
      return abs(muons[0].trkz0sintheta)>0.05 and abs(muons[1].trkz0sintheta)>0.05
    #__________________________________________________________________________
    def cut_MuLeadZ0SinThetaNot005(self):
      muons = self.store['muons']
      return abs(muons[0].trkz0sintheta)>0.05 
    #__________________________________________________________________________
    def cut_MuSubLeadZ0SinThetaNot005(self):
      muons = self.store['muons']
      return abs(muons[1].trkz0sintheta)>0.05 
    
    
    #__________________________________________________________________________
    def cut_AllMuPairsMedium(self):
      pairs = self.store['mu_pairs']
      passed = True
      
      for p in pairs:
        if "mc" in self.sampletype:
          if not (p.lead.isTruthMatchedToMuon and p.sublead.isTruthMatchedToMuon): continue
        passed = passed and p.lead.isMedium and p.sublead.isMedium
      return passed 
    
    #__________________________________________________________________________
    def cut_METlow40(self):
      met = self.store["met_clus"]
      return met.tlv.Pt() < 40 * GeV
    
    #__________________________________________________________________________
    def cut_METlow50(self):
      met = self.store["met_clus"]
      return met.tlv.Pt() < 50 * GeV
    
    #__________________________________________________________________________
    def cut_METlow30(self):
      met = self.store["met_clus"]
      return met.tlv.Pt() < 30 * GeV
    
    #__________________________________________________________________________
    def cut_METhigher10(self):
      met = self.store["met_clus"]
      return met.tlv.Pt() > 10 * GeV
    
    #__________________________________________________________________________
    def cut_METhigher40(self):
      met = self.store["met_clus"]
      return met.tlv.Pt() > 40 * GeV
    
    #__________________________________________________________________________
    def cut_METhigher50(self):
      met = self.store["met_clus"]
      return met.tlv.Pt() > 50 * GeV
   
    #__________________________________________________________________________
    def cut_SumCosDPhi02(self):
      met = self.store["met_clus"]
      lead_mu = self.store["muons"][0]
      lead_jet = None
      if self.store["jets"]:
        lead_jet = self.store["jets"][0]
      if lead_jet:
        scdphi = 0.0
        scdphi += ROOT.TMath.Cos(met.tlv.Phi() - lead_mu.tlv.Phi())
        scdphi += ROOT.TMath.Cos(met.tlv.Phi() - lead_jet.tlv.Phi())
        return scdphi > -0.2
      else: return False

    #__________________________________________________________________________
    def cut_MuJetDphi27(self):
      lead_mu = self.store["muons"][0]
      lead_jet = None
      if self.store["jets"]:
        lead_jet = self.store["jets"][0]
      if lead_jet:
        return abs(lead_mu.tlv.DeltaPhi(lead_jet.tlv)) > 2.7
      else: return False
    
    #__________________________________________________________________________
    def cut_MuJetDphi28(self):
      lead_mu = self.store["muons"][0]
      lead_jet = None
      if self.store["jets"]:
        lead_jet = self.store["jets"][0]
      if lead_jet:
        return abs(lead_mu.tlv.DeltaPhi(lead_jet.tlv)) > 2.8
      else: return False
    
    
    #__________________________________________________________________________
    def cut_MuJetDphi26(self):
      lead_mu = self.store["muons"][0]
      lead_jet = None
      if self.store["jets"]:
        lead_jet = self.store["jets"][0]
      if lead_jet:
        return abs(lead_mu.tlv.DeltaPhi(lead_jet.tlv)) > 2.6
      else: return False
    
    
    #__________________________________________________________________________
    def cut_MuJetDphi24(self):
      lead_mu = self.store["muons"][0]
      lead_jet = None
      if self.store["jets"]:
        lead_jet = self.store["jets"][0]
      if lead_jet:
        return abs(lead_mu.tlv.DeltaPhi(lead_jet.tlv)) > 2.4
      else: return False
    
    
    #__________________________________________________________________________
    def cut_AllJetPt25(self):
      if self.store["jets"]:
        jets = self.store["jets"]
        for j in jets:
          if j.tlv.Pt() < 25 * GeV: return False
      return True
    
    #__________________________________________________________________________
    def cut_AllJetPt35(self):
      if self.store["jets"]:
        jets = self.store["jets"]
        for j in jets:
          if j.tlv.Pt() < 35 * GeV: return False
      return True
    
    #__________________________________________________________________________
    def cut_AllJetPt40(self):
      if self.store["jets"]:
        jets = self.store["jets"]
        for j in jets:
          if j.tlv.Pt() < 35 * GeV: return False
      return True
    
    #__________________________________________________________________________
    def cut_PASS(self):
      return True
    
#------------------------------------------------------------------------------
class PlotAlg(pyframe.algs.CutFlowAlg,CutAlg):
    """

    For making a set of standard plots after each cut in a cutflow.  PlotAlg
    inherets from CutAlg so all the functionality from CutAlg is available for
    applying selection. In addition you can apply weights at different points
    in the selection.

    The selection should be configured by specifying 'cut_flow' in the
    constructor as such:

    cut_flow = [
        ['Cut1', ['Weight1a','Weight1b'],
        ['Cut2', ['Weight2']],
        ['Cut3', None],
        ...
        ]

    The weights must be available in the store.

    'region' will set the name of the dir where the plots are saved

    Inhereting from CutFlowAlg provides the functionality to produce cutflow
    histograms that will be named 'cutflow_<region>' and 'cutflow_raw_<region>'

    """
    #__________________________________________________________________________
    def __init__(self,
                 name     = 'PlotAlg',
                 region   = '',
                 obj_keys = [], # make cutflow hist for just this objects
                 cut_flow = None,
                 plot_all = True,
                 ):
        pyframe.algs.CutFlowAlg.__init__(self,key=region,obj_keys=obj_keys)
        CutAlg.__init__(self,name,isfilter=False)
        self.cut_flow = cut_flow
        self.region   = region
        self.plot_all = plot_all
        self.obj_keys = obj_keys
    
    #_________________________________________________________________________
    def initialize(self):
        pyframe.algs.CutFlowAlg.initialize(self)
    #_________________________________________________________________________
    def execute(self, weight):
   
        # next line fills in the cutflow hists
        # the first bin of the cutflow does not
        # take into account object weights
        pyframe.algs.CutFlowAlg.execute(self, weight)

        list_cuts = []
        for cut, list_weights in self.cut_flow:
            ## apply weights for this cut
            if list_weights:
              for w in list_weights: weight *= self.store[w]

            list_cuts.append(cut)
            passed = self.check_region(list_cuts)
            self.hists[self.region].count_if(passed, cut, weight)

            ## if plot_all is True, plot after each cut, 
            ## else only plot after full selection
            
            # obj cutflow is computed at the end of the cutflow
            #if len(list_cuts)==len(self.cut_flow):
            if self.obj_keys:
             for k in self.obj_keys:
              for o in self.store[k]:
               if hasattr(o,"cdict") and hasattr(o,"wdict"):
                obj_passed = True
                obj_weight = 1.0
                if list_weights:
                 for w in list_weights:
                  if w.startswith("MuPairs"):
                   obj_weight *= o.GetWeight(w) 
                for c in list_cuts:
                 if c.startswith("MuPairs"):
                  obj_passed = o.HasPassedCut(c) and obj_passed
                self.hists[self.region+"_"+k].count_if(obj_passed and passed, c, obj_weight * weight)
            
            if (self.plot_all or len(list_cuts)==len(self.cut_flow)):
               region_name = os.path.join(self.region,'_'.join(list_cuts))
               region_name = region_name.replace('!', 'N')
               region = os.path.join('/regions/', region_name)
               
               #if passed:             
               self.plot(region, passed, list_cuts, cut, list_weights=list_weights, weight=weight)

        return True

    #__________________________________________________________________________
    def finalize(self):
        pyframe.algs.CutFlowAlg.finalize(self)

    #__________________________________________________________________________
    def plot(self, region, passed, list_cuts, cut, list_weights=None, weight=1.0):
        
        # should probably make this configurable
        ## get event candidate
        muons      = self.store['muons'] 
        mu_lead    = muons[0]
        #mu_sublead = muons[1]
        jets       = self.store['jets']
        jet_lead   = jets[0]
        
        met_trk    = self.store['met_trk']
        met_clus   = self.store['met_clus']
        #mupairs    = self.store['mu_pairs']
        
        ## plot directories
        EVT    = os.path.join(region, 'event')
        MUONS  = os.path.join(region, 'muons')
        MET    = os.path.join(region, 'met')
        JETS   = os.path.join(region, 'jets')
        #PAIRS  = os.path.join(region, 'pairs')
        
        # -----------------
        # Create histograms
        # -----------------
        ## event plots
        self.h_averageIntPerXing = self.hist('h_averageIntPerXing', "ROOT.TH1F('$', ';averageInteractionsPerCrossing;Events', 50, -0.5, 49.5)", dir=EVT)
        self.h_actualIntPerXing = self.hist('h_actualIntPerXing', "ROOT.TH1F('$', ';actualInteractionsPerCrossing;Events', 50, -0.5, 49.5)", dir=EVT)
        self.h_NPV = self.hist('h_NPV', "ROOT.TH1F('$', ';NPV;Events', 35, 0., 35.0)", dir=EVT)
        self.h_nmuons = self.hist('h_nmuons', "ROOT.TH1F('$', ';N_{#mu};Events', 8, 0, 8)", dir=EVT)
        self.h_nelectrons = self.hist('h_nelectrons', "ROOT.TH1F('$', ';N_{e};Events', 8, 0, 8)", dir=EVT)
        self.h_njets = self.hist('h_njets', "ROOT.TH1F('$', ';N_{jet};Events', 8, 0, 8)", dir=EVT)
        #self.h_nmuonpairs = self.hist('h_nmuonpairs', "ROOT.TH1F('$', ';N_{#mu#mu};Events ', 8, 0, 8)", dir=EVT)
             
        #self.h_muons_chargeprod = self.hist('h_muons_chargeprod', "ROOT.TH1F('$', ';q(#mu_{lead}) #timesq (#mu_{sublead});Events ', 4, -2,2)", dir=EVT)
        #self.h_muons_dphi = self.hist('h_muons_dphi', "ROOT.TH1F('$', ';#Delta#phi(#mu_{lead},#mu_{sublead});Events ', 64, -3.2, 3.2)", dir=EVT)
        #self.h_muons_deta = self.hist('h_muons_deta', "ROOT.TH1F('$', ';#Delta#eta(#mu_{lead},#mu_{sublead});Events ', 50, -2.5, 2.5)", dir=EVT)
        #self.h_muons_mVis = self.hist('h_muons_mVis', "ROOT.TH1F('$', ';m_{vis}(#mu_{lead},#mu_{sublead}) [GeV];Events / (1 GeV)', 2000, 0.0, 2000.)", dir=EVT)
        #self.h_muons_mTtot = self.hist('h_muons_mTtot', "ROOT.TH1F('$', ';m^{tot}_{T}(#mu_{lead},#mu_{sublead}) [GeV];Events / (1 GeV)', 2000, 0.0, 2000.)", dir=EVT)
             
        self.h_mujet_dphi = self.hist('h_mujet_dphi', "ROOT.TH1F('$', ';#Delta#phi(#mu_{lead},jet_{lead});Events ', 64, -3.2, 3.2)", dir=EVT)
        self.h_scdphi = self.hist('h_scdphi', "ROOT.TH1F('$', ';#Sigma cos#Delta#phi;Events ', 400, -2., 2.)", dir=EVT)
        
        ## jets plots
        self.h_jetlead_pt = self.hist('h_jetlead_pt', "ROOT.TH1F('$', ';p_{T}(jet_{lead}) [GeV];Events / (1 GeV)', 2000, 0.0, 2000.0)", dir=JETS)


        ## muon plots
        # leading
        self.h_mulead_pt = self.hist('h_mulead_pt', "ROOT.TH1F('$', ';p_{T}(#mu_{lead}) [GeV];Events / (1 GeV)', 2000, 0.0, 2000.0)", dir=MUONS)
        self.h_mulead_eta = self.hist('h_mulead_eta', "ROOT.TH1F('$', ';#eta(#mu_{lead});Events / (0.1)', 50, -2.5, 2.5)", dir=MUONS)
        self.h_mulead_phi = self.hist('h_mulead_phi', "ROOT.TH1F('$', ';#phi(#mu_{lead});Events / (0.1)', 64, -3.2, 3.2)", dir=MUONS)
        self.h_mulead_trkd0 = self.hist('h_mulead_trkd0', "ROOT.TH1F('$', ';d^{trk}_{0}(#mu_{lead}) [mm];Events / (0.01)', 80, -0.4, 0.4)", dir=MUONS)
        self.h_mulead_trkd0sig = self.hist('h_mulead_trkd0sig', "ROOT.TH1F('$', ';d^{trk sig}_{0}(#mu_{lead});Events / (0.1)', 100, 0., 10.)", dir=MUONS)
        self.h_mulead_trkz0 = self.hist('h_mulead_trkz0', "ROOT.TH1F('$', ';z^{trk}_{0}(#mu_{lead}) [mm];Events / (0.1)', 40, -2, 2)", dir=MUONS)
        self.h_mulead_trkz0sintheta = self.hist('h_mulead_trkz0sintheta', "ROOT.TH1F('$', ';z^{trk}_{0}sin#theta(#mu_{lead}) [mm];Events / (0.01)', 200, -1, 1)", dir=MUONS)
              
        self.h_mulead_topoetcone20 = self.hist('h_mulead_topoetcone20', "ROOT.TH1F('$', ';topoetcone20/p_{T}(#mu_{lead}); Events / 0.001', 10000, 0.0, 10.0)", dir=MUONS)
        self.h_mulead_topoetcone30 = self.hist('h_mulead_topoetcone30', "ROOT.TH1F('$', ';topoetcone30/p_{T}(#mu_{lead}); Events / 0.001', 10000, 0.0, 10.0)", dir=MUONS)
        self.h_mulead_topoetcone40 = self.hist('h_mulead_topoetcone40', "ROOT.TH1F('$', ';topoetcone40/p_{T}(#mu_{lead}); Events / 0.001', 10000, 0.0, 10.0)", dir=MUONS)
        self.h_mulead_ptvarcone20 = self.hist('h_mulead_ptvarcone20', "ROOT.TH1F('$', ';ptvarcone20/p_{T}(#mu_{lead}); Events / 0.001', 10000, 0.0, 10.0)", dir=MUONS)
        self.h_mulead_ptvarcone30 = self.hist('h_mulead_ptvarcone30', "ROOT.TH1F('$', ';ptvarcone30/p_{T}(#mu_{lead}); Events / 0.001', 10000, 0.0, 10.0)", dir=MUONS)
        self.h_mulead_ptvarcone40 = self.hist('h_mulead_ptvarcone40', "ROOT.TH1F('$', ';ptvarcone40/p_{T}(#mu_{lead}); Events / 0.001', 10000, 0.0, 10.0)", dir=MUONS)
              
        self.h_mulead_ptcone20 = self.hist('h_mulead_ptcone20', "ROOT.TH1F('$', ';ptcone20/p_{T}(#mu_{lead}); Events / 0.001', 10000, 0.0, 10.0)", dir=MUONS)
        self.h_mulead_ptcone30 = self.hist('h_mulead_ptcone30', "ROOT.TH1F('$', ';ptcone30/p_{T}(#mu_{lead}); Events / 0.001', 10000, 0.0, 10.0)", dir=MUONS)
        self.h_mulead_ptcone40 = self.hist('h_mulead_ptcone40', "ROOT.TH1F('$', ';ptcone40/p_{T}(#mu_{lead}); Events / 0.001', 10000, 0.0, 10.0)", dir=MUONS)
        
        
        # subleading
        """
        self.h_musublead_pt = self.hist('h_musublead_pt', "ROOT.TH1F('$', ';p_{T}(#mu_{sublead}) [GeV];Events / (1 GeV)', 2000, 0.0, 2000.0)", dir=MUONS)
        self.h_musublead_eta = self.hist('h_musublead_eta', "ROOT.TH1F('$', ';#eta(#mu_{sublead});Events / (0.1)', 50, -2.5, 2.5)", dir=MUONS)
        self.h_musublead_phi = self.hist('h_musublead_phi', "ROOT.TH1F('$', ';#phi(#mu_{sublead});Events / (0.1)', 64, -3.2, 3.2)", dir=MUONS)
        self.h_musublead_trkd0 = self.hist('h_musublead_trkd0', "ROOT.TH1F('$', ';d^{trk}_{0}(#mu_{sublead}) [mm];Events / (0.01)', 80, -0.4, 0.4)", dir=MUONS)
        self.h_musublead_trkd0sig = self.hist('h_musublead_trkd0sig', "ROOT.TH1F('$', ';d^{trk sig}_{0}(#mu_{sublead});Events / (0.1)', 100, 0., 10.)", dir=MUONS)
        self.h_musublead_trkz0 = self.hist('h_musublead_trkz0', "ROOT.TH1F('$', ';z^{trk}_{0}(#mu_{sublead}) [mm];Events / (0.1)', 40, -2, 2)", dir=MUONS)
        self.h_musublead_trkz0sintheta = self.hist('h_musublead_trkz0sintheta', "ROOT.TH1F('$', ';z^{trk}_{0}sin#theta(#mu_{sublead}) [mm];Events / (0.01)', 200, -1, 1)", dir=MUONS)
              
        self.h_musublead_topoetcone20 = self.hist('h_musublead_topoetcone20', "ROOT.TH1F('$', ';topoetcone20/p_{T}(#mu_{sublead}); Events / 0.001', 10000, 0.0, 10.0)", dir=MUONS)
        self.h_musublead_topoetcone30 = self.hist('h_musublead_topoetcone30', "ROOT.TH1F('$', ';topoetcone30/p_{T}(#mu_{sublead}); Events / 0.001', 10000, 0.0, 10.0)", dir=MUONS)
        self.h_musublead_topoetcone40 = self.hist('h_musublead_topoetcone40', "ROOT.TH1F('$', ';topoetcone40/p_{T}(#mu_{sublead}); Events / 0.001', 10000, 0.0, 10.0)", dir=MUONS)
        self.h_musublead_ptvarcone20 = self.hist('h_musublead_ptvarcone20', "ROOT.TH1F('$', ';ptvarcone20/p_{T}(#mu_{sublead}); Events / 0.001', 10000, 0.0, 10.0)", dir=MUONS)
        self.h_musublead_ptvarcone30 = self.hist('h_musublead_ptvarcone30', "ROOT.TH1F('$', ';ptvarcone30/p_{T}(#mu_{sublead}); Events / 0.001', 10000, 0.0, 10.0)", dir=MUONS)
        self.h_musublead_ptvarcone40 = self.hist('h_musublead_ptvarcone40', "ROOT.TH1F('$', ';ptvarcone40/p_{T}(#mu_{sublead}); Events / 0.001', 10000, 0.0, 10.0)", dir=MUONS)
              
        self.h_musublead_ptcone20 = self.hist('h_musublead_ptcone20', "ROOT.TH1F('$', ';ptcone20/p_{T}(#mu_{sublead}); Events / 0.001', 10000, 0.0, 10.0)", dir=MUONS)
        self.h_musublead_ptcone30 = self.hist('h_musublead_ptcone30', "ROOT.TH1F('$', ';ptcone30/p_{T}(#mu_{sublead}); Events / 0.001', 10000, 0.0, 10.0)", dir=MUONS)
        self.h_musublead_ptcone40 = self.hist('h_musublead_ptcone40', "ROOT.TH1F('$', ';ptcone40/p_{T}(#mu_{sublead}); Events / 0.001', 10000, 0.0, 10.0)", dir=MUONS)
        
        """ 
        ## met plots
        self.h_met_clus_et = self.hist('h_met_clus_et', "ROOT.TH1F('$', ';E^{miss}_{T}(clus) [GeV];Events / (1 GeV)', 2000, 0.0, 2000.0)", dir=MET)
        self.h_met_clus_phi = self.hist('h_met_clus_phi', "ROOT.TH1F('$', ';#phi(E^{miss}_{T}(clus));Events / (0.1)', 64, -3.2, 3.2)", dir=MET)
        self.h_met_trk_et = self.hist('h_met_trk_et', "ROOT.TH1F('$', ';E^{miss}_{T}(trk) [GeV];Events / (1 GeV)', 2000, 0.0, 2000.0)", dir=MET)
        self.h_met_trk_phi = self.hist('h_met_trk_phi', "ROOT.TH1F('$', ';#phi(E^{miss}_{T}(trk));Events / (0.1)', 64, -3.2, 3.2)", dir=MET)
        self.h_met_clus_sumet = self.hist('h_met_clus_sumet', "ROOT.TH1F('$', ';#Sigma E_{T}(clus) [GeV];Events / (1 GeV)', 2000, 0.0, 2000.0)", dir=MET)
        self.h_met_trk_sumet = self.hist('h_met_trk_sumet', "ROOT.TH1F('$', ';#Sigma E_{T}(trk) [GeV];Events / (1 GeV)', 2000, 0.0, 2000.0)", dir=MET)
        
        ## muons pairs
        """
        self.h_mumu_mVis = self.hist('h_mumu_mVis', "ROOT.TH1F('$', ';m_{vis}(#mu#mu) [GeV];Events / (1 GeV)', 2000, 0.0, 2000.0)", dir=PAIRS)
        self.h_mumu_mTtot = self.hist('h_mumu_mTtot', "ROOT.TH1F('$', ';m^{tot}_{T}(#mu#mu) [GeV];Events / (1 GeV)', 2000, 0.0, 2000.0)", dir=PAIRS)
        self.h_mumu_angle = self.hist('h_mumu_angle', "ROOT.TH1F('$', ';#omega(#mu#mu);Events', 320, 0.0, 3.2)", dir=PAIRS)
        self.h_mumu_sumcosdphi = self.hist('h_mumu_sumcosdphi', "ROOT.TH1F('$', ';#Sigmacos#Delta#phi(#mu_{lead/sublead},E^{miss}_{T});Events / 0.1', 40, -2, 2)", dir=PAIRS)
        self.h_mumu_mulead_pt = self.hist('h_mumu_mulead_pt', "ROOT.TH1F('$', ';p_{T}(#mu#mu_{lead}) [GeV];Events / (1 GeV)', 2000, 0.0, 2000.0)", dir=PAIRS)
        self.h_mumu_musublead_pt = self.hist('h_mumu_musublead_pt', "ROOT.TH1F('$', ';p_{T}(#mu#mu_{sublead}) [GeV];Events / (1 GeV)',2000,0.0,2000.0)",dir=PAIRS)
        self.h_mumu_mulead_eta = self.hist('h_mumu_mulead_eta', "ROOT.TH1F('$', ';#eta(#mu#mu_{lead});Events / (0.1)', 50, -2.5, 2.5)", dir=PAIRS)
        self.h_mumu_musublead_eta = self.hist('h_mumu_musublead_eta', "ROOT.TH1F('$', ';#eta(#mu#mu_{sublead});Events / (0.1)', 50, -2.5, 2.5)", dir=PAIRS)
        self.h_mumu_mulead_phi = self.hist('h_mumu_mulead_phi', "ROOT.TH1F('$', ';#phi(#mu#mu_{lead});Events / (0.1)', 64, -3.2, 3.2)", dir=PAIRS)
        self.h_mumu_musublead_phi = self.hist('h_mumu_musublead_phi', "ROOT.TH1F('$', ';#phi(#mu#mu_{sublead});Events / (0.1)', 64, -3.2, 3.2)", dir=PAIRS)
        """ 
        
        # ---------------
        # Fill histograms
        # ---------------
        if passed:
          ## event plots
          self.h_averageIntPerXing.Fill(self.chain.averageInteractionsPerCrossing, weight)
          self.h_actualIntPerXing.Fill(self.chain.actualInteractionsPerCrossing, weight)
          self.h_NPV.Fill(self.chain.NPV, weight)
          self.h_nmuons.Fill(self.chain.nmuon, weight)
          self.h_nelectrons.Fill(self.chain.nel, weight)
          self.h_njets.Fill(self.chain.njets, weight)
          #self.h_nmuonpairs.Fill(len(mupairs), weight)
          
          """
          if bool(len(muons)==2):
            self.h_muons_chargeprod.Fill(self.store['charge_product'], weight)
            self.h_muons_dphi.Fill(self.store['muons_dphi'], weight)
            self.h_muons_deta.Fill(self.store['muons_deta'], weight)
            self.h_muons_mVis.Fill(self.store['mVis']/GeV, weight)
            self.h_muons_mTtot.Fill(self.store['mTtot']/GeV, weight)
          """ 

          if bool(len(jets)) and bool(len(muons)):
            self.h_mujet_dphi.Fill(self.store['mujet_dphi'], weight)
            self.h_scdphi.Fill(self.store['scdphi'], weight)
         
          ## jets plots
          #if bool(len(jets)):
          #  self.h_jetlead_pt.Fill(jet_lead.tlv.Pt()/GeV, weight)
          
          
          ## muon plots
          # leading
          self.h_mulead_pt.Fill(mu_lead.tlv.Pt()/GeV, weight)
          self.h_mulead_eta.Fill(mu_lead.tlv.Eta(), weight)
          self.h_mulead_phi.Fill(mu_lead.tlv.Phi(), weight)
          self.h_mulead_trkd0.Fill(mu_lead.trkd0, weight)
          self.h_mulead_trkd0sig.Fill(mu_lead.trkd0sig, weight)
          self.h_mulead_trkz0.Fill(mu_lead.trkz0, weight)
          self.h_mulead_trkz0sintheta.Fill(mu_lead.trkz0sintheta, weight)
         
          self.h_mulead_topoetcone20.Fill(mu_lead.topoetcone20/mu_lead.tlv.Pt(), weight)
          self.h_mulead_topoetcone30.Fill(mu_lead.topoetcone30/mu_lead.tlv.Pt(), weight)
          self.h_mulead_topoetcone40.Fill(mu_lead.topoetcone40/mu_lead.tlv.Pt(), weight)
          self.h_mulead_ptvarcone20.Fill(mu_lead.ptvarcone20/mu_lead.tlv.Pt(), weight)
          self.h_mulead_ptvarcone30.Fill(mu_lead.ptvarcone30/mu_lead.tlv.Pt(), weight)
          self.h_mulead_ptvarcone40.Fill(mu_lead.ptvarcone40/mu_lead.tlv.Pt(), weight)
         
          self.h_mulead_ptcone20.Fill(mu_lead.ptcone20/mu_lead.tlv.Pt(), weight)
          self.h_mulead_ptcone30.Fill(mu_lead.ptcone30/mu_lead.tlv.Pt(), weight)
          self.h_mulead_ptcone40.Fill(mu_lead.ptcone40/mu_lead.tlv.Pt(), weight)
         
         
          # subleading
          """
          self.h_musublead_pt.Fill(mu_sublead.tlv.Pt()/GeV, weight)
          self.h_musublead_eta.Fill(mu_sublead.tlv.Eta(), weight)
          self.h_musublead_phi.Fill(mu_sublead.tlv.Phi(), weight)
          self.h_musublead_trkd0.Fill(mu_sublead.trkd0, weight)
          self.h_musublead_trkd0sig.Fill(mu_sublead.trkd0sig, weight)
          self.h_musublead_trkz0.Fill(mu_sublead.trkz0, weight)
          self.h_musublead_trkz0sintheta.Fill(mu_sublead.trkz0sintheta, weight)
          
          self.h_musublead_topoetcone20.Fill(mu_sublead.topoetcone20/mu_sublead.tlv.Pt(), weight)
          self.h_musublead_topoetcone30.Fill(mu_sublead.topoetcone30/mu_sublead.tlv.Pt(), weight)
          self.h_musublead_topoetcone40.Fill(mu_sublead.topoetcone40/mu_sublead.tlv.Pt(), weight)
          self.h_musublead_ptvarcone20.Fill(mu_sublead.ptvarcone20/mu_sublead.tlv.Pt(), weight)
          self.h_musublead_ptvarcone30.Fill(mu_sublead.ptvarcone30/mu_sublead.tlv.Pt(), weight)
          self.h_musublead_ptvarcone40.Fill(mu_sublead.ptvarcone40/mu_sublead.tlv.Pt(), weight)
          
          self.h_musublead_ptcone20.Fill(mu_sublead.ptcone20/mu_sublead.tlv.Pt(), weight)
          self.h_musublead_ptcone30.Fill(mu_sublead.ptcone30/mu_sublead.tlv.Pt(), weight)
          self.h_musublead_ptcone40.Fill(mu_sublead.ptcone40/mu_sublead.tlv.Pt(), weight)
          """ 
          
          ## met plots
          self.h_met_clus_et.Fill(met_clus.tlv.Pt()/GeV, weight)
          self.h_met_clus_phi.Fill(met_clus.tlv.Phi(), weight)
          self.h_met_trk_et.Fill(met_trk.tlv.Pt()/GeV, weight)
          self.h_met_trk_phi.Fill(met_trk.tlv.Phi(), weight)
          self.h_met_clus_sumet.Fill(met_clus.sumet/GeV, weight)
          self.h_met_trk_sumet.Fill(met_trk.sumet/GeV, weight)
          
          """
          ## muon pairs plots
          for mp in mupairs:
           
            pcut = True 
            for c in list_cuts:
             if c.startswith("MuPairs"):
              #print c, mp.angle, mp.HasPassedCut(c)
              pcut = pcut and mp.HasPassedCut(c)
             
            pweight = 1.0
            if list_weights:
             for w in list_weights: 
              if w.startswith("MuPairs"):
               pweight *= mp.GetWeight(w)
            
            if pcut: 
             #if mp.angle < 1.0 or mp.angle > 2.5: print "What the fuck"
             self.h_mumu_angle.Fill(mp.angle, pweight * weight)
             self.h_mumu_mVis.Fill(mp.m_vis/GeV, pweight * weight)
             self.h_mumu_mTtot.Fill(mp.mt_tot/GeV, pweight * weight)
             self.h_mumu_sumcosdphi.Fill(mp.SumCosDphi, pweight * weight)
             self.h_mumu_mulead_pt.Fill(mp.lead.tlv.Pt()/GeV, pweight * weight)
             self.h_mumu_musublead_pt.Fill(mp.sublead.tlv.Pt()/GeV,pweight*weight)
             self.h_mumu_mulead_eta.Fill(mp.lead.tlv.Eta(), pweight * weight)
             self.h_mumu_musublead_eta.Fill(mp.sublead.tlv.Eta(), pweight * weight)
             self.h_mumu_mulead_phi.Fill(mp.lead.tlv.Phi(), pweight * weight)
             self.h_mumu_musublead_phi.Fill(mp.sublead.tlv.Phi(), pweight * weight)
          """   
    
    #__________________________________________________________________________
    def check_region(self,cutnames):
        cut_passed = True
        for cn in cutnames:
            ## could use this to fail when cuts not available
            #if not cuts.has_key(cn): return False
    
            ## pass if None
            if cn == 'ALL': continue
            #if cn.startswith("MuPairs"): continue

            if cn.startswith('!'):
                cut_passed = not self.apply_cut(cn[1:])
            else:
                cut_passed = self.apply_cut(cn) and cut_passed
            #if not cut_passed:
            #    return False
        return cut_passed
    
    
    """ 
    #__________________________________________________________________________
    def get_obj_cutflow(self, obj_key, cut, list_weights=None, cut_prefix=""):
        for o in self.store[obj_key]:
          if hasattr(o,"cdict") and hasattr(o,"wdict"):
            obj_weight = 1.0
            if list_weights: 
              for w in list_weights:
                obj_weight *= o.GetWeight(w)
                if cut_prefix: 
                  if cut.startswith(cut_prefix): 
                    obj_passed = o.HasPassedCut(cut) and passed
            self.hists[self.region+"_"+obj_key].count_if(obj_passed, cut, obj_weight * weight)
    """

    #__________________________________________________________________________
    def reset_attributes(self,objects):
        for o in objects:
          o.ResetCuts()
          o.ResetWeights()
        return 

#------------------------------------------------------------------------------
class VarsAlg(pyframe.core.Algorithm):
    """
    
    calcualtes derived quantities, like masses, dphi etc...

    """
    #__________________________________________________________________________
    def __init__(self, 
                 name ='VarsAlg',
                 key_muons = 'muons',
                 key_jets = 'jets',
                 key_met = 'met_clus',
                 ):
        pyframe.core.Algorithm.__init__(self, name)
        self.key_muons = key_muons
        self.key_jets = key_jets
        self.key_met = key_met

    #__________________________________________________________________________
    def execute(self, weight):
        pyframe.core.Algorithm.execute(self, weight)
        """
        computes variables and puts them in the store
        """

        ## get objects from event candidate
        ## --------------------------------------------------
        assert self.store.has_key(self.key_muons), "muons key: %s not found in store!" % (self.key_muons)
        muons = self.store[self.key_muons]
        jets = self.store[self.key_jets]
        met = self.store[self.key_met]

        #assert len(muons)>=2, "less than 2 muons in event!"
        
        #assert self.store.has_key(self.key_met), "met key: %s not found in store!" % (self.key_met)
        #met = self.store[self.key_met]

        ## evaluate vars
        ## --------------------------------------------------           
        if bool(len(muons)==2):
          muon1 = muons[0]
          muon1T = ROOT.TLorentzVector()
          muon1T.SetPtEtaPhiM( muon1.tlv.Pt(), 0., muon1.tlv.Phi(), muon1.tlv.M() )
          muon2 = muons[1]
          muon2T = ROOT.TLorentzVector()
          muon2T.SetPtEtaPhiM( muon2.tlv.Pt(), 0., muon2.tlv.Phi(), muon2.tlv.M() )
        
          self.store['charge_product'] = muon2.trkcharge*muon1.trkcharge
          self.store['mVis']           = (muon2.tlv+muon1.tlv).M()
          self.store['mTtot']          = (muon1T + muon2T + met.tlv).M()  
          self.store['muons_dphi']     = muon2.tlv.DeltaPhi(muon1.tlv)
          self.store['muons_deta']     = muon2.tlv.Eta()-muon1.tlv.Eta()
          
          # definition of tag and probe 
          """
          lead_mu_is_tight = bool(muon1.isIsolated_FixedCutTightTrackOnly and muon1.trkd0sig<3.)
          lead_mu_is_loose = bool(not muon1.isIsolated_FixedCutTightTrackOnly and muon1.trkd0sig<10.)

          sublead_mu_is_tight = bool(muon2.isIsolated_FixedCutTightTrackOnly and muon2.trkd0sig<3.)
          sublead_mu_is_loose = bool(not muon2.isIsolated_FixedCutTightTrackOnly and muon2.trkd0sig<10.)
          
          if lead_mu_is_tight and sublead_mu_is_tight:
            if muon1.trkcharge > 0.0:
              self.store['tag'] = copy(muon1)
              self.store['probe'] = copy(muon2) 
            else:
              self.store['tag'] = copy(muon2)
              self.store['probe'] = copy(muon1) 
          elif lead_mu_is_loose or sublead_mu_is_tight:
            self.store['tag'] = copy(muon2)
            self.store['probe'] = copy(muon1) 
          elif sublead_mu_is_loose or lead_mu_is_tight:
            self.store['tag'] = copy(muon1)
            self.store['probe'] = copy(muon2) 
          """ 
        
        if bool(len(jets)) and bool(len(muons)):
          self.store['mujet_dphi'] = muons[0].tlv.DeltaPhi(jets[0].tlv)
          scdphi = 0.0
          scdphi += ROOT.TMath.Cos(met.tlv.Phi() - muons[0].tlv.Phi())
          scdphi += ROOT.TMath.Cos(met.tlv.Phi() - jets[0].tlv.Phi())
          self.store['scdphi'] = scdphi

        return True


#__________________________________________________________________________
def log_bins(nbins,xmin,xmax):
    xmin_log = math.log(xmin)
    xmax_log = math.log(xmax)
    log_bins = [ float(i)/float(nbins)*(xmax_log-xmin_log) + xmin_log for i in xrange(nbins+1)]
    bins = [ math.exp(x) for x in log_bins ]
    return bins

#__________________________________________________________________________
def log_bins_str(nbins,xmin,xmax):
    bins = log_bins(nbins,xmin,xmax)
    bins_str = "%d, array.array('f',%s)" % (len(bins)-1, str(bins))
    return bins_str 



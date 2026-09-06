import json
import re
from typing import Dict, Any, List
from app.schemas.ai import DisputeClaimRequest, DisputeClaimResponse
from app.services.ai.gemini_client import GeminiClient


class DisputeService:
    """Automated Dispute & SAFE-T Claim Drafter for Amazon India and Flipkart Seller Support."""

    @classmethod
    def draft_dispute(cls, req: DisputeClaimRequest) -> DisputeClaimResponse:
        mkt = req.marketplace.lower()
        order_id = req.order_id.strip()
        loss_val = f"₹{req.loss_amount:,.2f}"
        claim_type = req.claim_type.lower()
        user_notes = (req.notes or "").strip()

        # 1. Attempt AI Generation via Gemini
        if GeminiClient.is_configured():
            prompt = (
                f"You are an expert e-commerce dispute resolution specialist for Indian marketplace sellers.\n"
                f"Draft an assertive, evidence-backed dispute / reimbursement claim letter for {req.marketplace.upper()}.\n\n"
                f"Details:\n"
                f"- Order ID: {order_id}\n"
                f"- Claim Type: {req.claim_type}\n"
                f"- Financial Loss Claimed: {loss_val}\n"
                f"- Seller Inspection Notes: {user_notes or 'Standard incident report'}\n\n"
                f"Return a strict JSON object with this exact structure:\n"
                "{\n"
                '  "subject_line": "Official ticket subject line with order ID",\n'
                '  "policy_citation": "Exact Amazon SAFE-T or Flipkart SPF policy citation",\n'
                '  "formal_claim_letter": "Full professional formal letter body with paragraphs, incident summary, loss claim, and request for reimbursement",\n'
                '  "required_evidence_checklist": [\n'
                '    "Evidence bullet 1",\n'
                '    "Evidence bullet 2",\n'
                '    "Evidence bullet 3",\n'
                '    "Evidence bullet 4"\n'
                '  ]\n'
                "}\n"
                "Return ONLY the JSON object."
            )
            raw_ai = GeminiClient.generate_text(
                prompt=prompt,
                system_instruction="You draft legal-grade, formal merchant dispute claims for Amazon India SAFE-T and Flipkart SPF portals.",
            )
            if raw_ai:
                try:
                    clean_json = re.sub(r"^```(?:json)?\n?", "", raw_ai.strip(), flags=re.MULTILINE)
                    clean_json = re.sub(r"\n?```$", "", clean_json.strip(), flags=re.MULTILINE)
                    parsed = json.loads(clean_json)
                    if parsed.get("subject_line") and parsed.get("formal_claim_letter"):
                        return DisputeClaimResponse(
                            claim_type=claim_type,
                            marketplace=mkt,
                            subject_line=parsed["subject_line"],
                            formal_claim_letter=parsed["formal_claim_letter"],
                            required_evidence_checklist=parsed.get("required_evidence_checklist", []),
                            policy_citation=parsed.get("policy_citation", "Marketplace Seller Protection Policy"),
                        )
                except Exception:
                    pass

        # 2. Resilient Template Fallback


        if mkt == "amazon":
            if "wrong" in claim_type or "fraud" in claim_type or "switch" in claim_type:
                subject = f"SAFE-T Claim Submission: Order #{order_id} - Materially Different / Fraudulent Return Received"
                policy = "Amazon India SAFE-T Policy - Reimbursement for Materially Different Customer Returns (Section 3.2)"
                letter = (
                    f"Dear Amazon India SAFE-T Review Team,\n\n"
                    f"We are formally submitting a SAFE-T reimbursement claim for Order ID: {order_id}.\n\n"
                    f"1. ISSUE DESCRIPTION:\n"
                    f"The customer initiated a return; however, the package delivered by EasyShip courier contained a materially different item rather than our original merchandise. "
                    f"{f'Note from inspection: {user_notes}' if user_notes else 'Upon opening the sealed return flyer, the returned item was found to be a completely different product / counterfeit substitute.'}\n\n"
                    f"2. FINANCIAL LOSS:\n"
                    f"Cost of product write-off and wasted shipping: {loss_val}.\n\n"
                    f"3. SUBMITTED EVIDENCE:\n"
                    f"We have captured continuous, uncut video documentation of the unboxing process clearly showing the Amazon return tracking label (LPN/AWB), the sealed bag condition, and the substituted contents.\n\n"
                    f"In accordance with Amazon Seller Central SAFE-T reimbursement guidelines, we kindly request full reimbursement of {loss_val} to our seller account disbursements.\n\n"
                    f"Respectfully,\n"
                    f"Seller Operations Team\n"
                    f"Apex Retail India"
                )
                evidence = [
                    "Continuous uncut video of opening the EasyShip return flyer showing the AWB / tracking barcode clearly.",
                    "High-resolution photos of the outer packaging with all 4 sides.",
                    "Close-up photo of the received incorrect item showing serial numbers or tags.",
                    "Original GST Tax Invoice showing product cost and serial/batch number.",
                ]
            elif "damage" in claim_type or "transit" in claim_type:
                subject = f"SAFE-T Claim Submission: Order #{order_id} - Damaged in Transit (EasyShip Courier Damage)"
                policy = "Amazon India SAFE-T Policy - Reimbursement for Products Damaged during Courier Transit (Section 2.1)"
                letter = (
                    f"Dear Amazon India SAFE-T Review Team,\n\n"
                    f"We hereby lodge a formal claim for Order ID: {order_id}, which was returned in a severely broken / unsellable state caused by transit handling.\n\n"
                    f"1. DISPATCH INTEGRITY:\n"
                    f"Our original shipment was dispatched in 5-ply protective packaging meeting all Amazon packaging specifications.\n\n"
                    f"2. DAMAGE OBSERVED:\n"
                    f"{f'Inspection details: {user_notes}' if user_notes else 'The outer courier flyer and internal carton arrived crushed, resulting in total destruction of the internal product.'}\n\n"
                    f"3. CLAIM VALUE:\n"
                    f"Total unrecoverable loss: {loss_val}.\n\n"
                    f"Please review the attached unboxing footage and process reimbursement for the damaged inventory.\n\n"
                    f"Respectfully,\n"
                    f"Seller Operations Team"
                )
                evidence = [
                    "Photos showing the crushed / torn outer Amazon courier flyer.",
                    "Unboxing video demonstrating that internal protective packaging was present but damaged by courier impact.",
                    "Clear photograph of the damaged product displaying the damage point.",
                    "Original Purchase/Manufacturing GST Invoice.",
                ]
            else:  # Weight discrepancy
                subject = f"Seller Support Dispute: Order #{order_id} - EasyShip Weight Discrepancy Overcharge"
                policy = "Amazon India Weight Handling Dispute Guidelines - Policy Schedule B"
                letter = (
                    f"Dear Amazon Seller Support Team,\n\n"
                    f"We are disputing an inaccurate weight handling charge applied to Order ID: {order_id}.\n\n"
                    f"1. DISCREPANCY SUMMARY:\n"
                    f"Amazon EasyShip billed this shipment at an excessive volumetric/dead weight slab. Our physical SKU weight is under 500g, while EasyShip billed for 1.5kg+.\n\n"
                    f"2. EXCESS FEE REVERSAL REQUESTED:\n"
                    f"Disputed excess shipping fee: {loss_val}.\n\n"
                    f"3. DOCUMENTATION:\n"
                    f"Attached please find photographic proof of the packaged SKU resting on a calibrated digital weighing scale with dimensional tape measurements (Length x Breadth x Height).\n\n"
                    f"We request immediate credit note adjustment for the excess weight handling charge.\n\n"
                    f"Respectfully,\n"
                    f"Apex Retail India"
                )
                evidence = [
                    "Photograph of packed product on a digital weighing scale showing weight clearly in grams.",
                    "Photographs measuring Length, Width, and Height with a measuring tape.",
                    "Copy of product catalog dimensions showing dead and volumetric weight.",
                ]
        else:  # Flipkart
            subject = f"Flipkart Seller Hub SPF Claim: Order ID #{order_id} - Return Incident Reimbursement"
            policy = "Flipkart Seller Protection Fund (SPF) Policy - Chapter 4: Claims for Lost/Damaged/Fake Returns"
            letter = (
                f"Dear Flipkart Seller Support Team,\n\n"
                f"We are filing a Seller Protection Fund (SPF) claim regarding Order ID #{order_id}.\n\n"
                f"INCIDENT SUMMARY:\n"
                f"{user_notes or 'The return item handed over by Ekart logistics was severely damaged / mismatched with original dispatched inventory.'}\n\n"
                f"CLAIM AMOUNT:\n"
                f"Total claimed loss: {loss_val}.\n\n"
                f"In accordance with Flipkart SPF rules, we have preserved the outer Ekart shipping bag with barcode intact and recorded the full unboxing inspection.\n\n"
                f"Kindly approve SPF reimbursement at your earliest convenience.\n\n"
                f"Regards,\n"
                f"Apex Retail India"
            )
            evidence = [
                "Uncut video recording of the package opening with Ekart tracking label readable.",
                "Photos of outer bag with all barcodes and shipping tags.",
                "Original GST tax invoice of the item.",
                "SPF incident form filled on Flipkart Seller Hub.",
            ]

        return DisputeClaimResponse(
            claim_type=claim_type,
            marketplace=mkt,
            subject_line=subject,
            formal_claim_letter=letter,
            required_evidence_checklist=evidence,
            policy_citation=policy,
        )


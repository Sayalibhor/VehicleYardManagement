import json
import time
import requests
from datetime import datetime
from flask import current_app
from models import db, SAPOutboundEvent

class SAPIntegrationService:

    @staticmethod
    def process_pending_events(batch_size: int = 20):
        pending_events = SAPOutboundEvent.query.filter(
            SAPOutboundEvent.sync_status.in_(["PENDING", "FAILED"]),
            SAPOutboundEvent.retry_count < current_app.config.get("SAP_MAX_RETRIES", 3)
        ).order_by(SAPOutboundEvent.created_at.asc()).limit(batch_size).all()

        results = {"processed": 0, "successful": 0, "failed": 0}

        for event in pending_events:
            results["processed"] += 1
            payload_data = json.loads(event.payload)

            if current_app.config.get("SAP_MOCK_MODE", True):
                event.sync_status = "SYNCED"
                event.sap_response = json.dumps({
                    "status": "200_OK",
                    "sapDocNum": f"SAP-YARD-{int(time.time())}-{event.event_id}",
                    "message": "Event successfully posted to SAP S/4HANA."
                })
                event.processed_at = datetime.utcnow()
                results["successful"] += 1
                continue

            try:
                headers = {
                    "Content-Type": "application/json",
                    "Authorization": current_app.config.get("SAP_AUTH_TOKEN", "")
                }
                resp = requests.post(
                    current_app.config["SAP_CPI_ENDPOINT"],
                    json=payload_data,
                    headers=headers,
                    timeout=5
                )

                if resp.status_code in [200, 201]:
                    event.sync_status = "SYNCED"
                    event.sap_response = resp.text
                    event.processed_at = datetime.utcnow()
                    results["successful"] += 1
                else:
                    event.retry_count += 1
                    event.sync_status = "FAILED"
                    event.sap_response = f"HTTP {resp.status_code}: {resp.text}"
                    results["failed"] += 1

            except Exception as ex:
                event.retry_count += 1
                event.sync_status = "FAILED"
                event.sap_response = str(ex)
                results["failed"] += 1

        db.session.commit()
        return results
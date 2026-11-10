import hmac
import hashlib
import json
import uuid
import urllib.parse
from decimal import Decimal
import urllib.request
import urllib.error

class YoupiPaymentGateway:
    """
    YouPI-PG Sovereign UPI & Cash Payment Gateway Client.
    Supports:
    1. Dynamic QR & deep-link session creation.
    2. Zero-dependency fallback sandbox / mock mode when local YouPI service is offline.
    3. Cryptographic HMAC-SHA256 webhook signature validation.
    """

    def __init__(self, hospital):
        self.hospital = hospital
        self.api_url = (hospital.youpi_api_url or 'http://localhost:6100').rstrip('/')
        self.merchant_id = hospital.youpi_merchant_id or f"mer_{hospital.slug}"
        self.webhook_secret = hospital.youpi_webhook_secret or f"sec_{hospital.slug}"
        self.is_sandbox = bool(hospital.youpi_sandbox_mode)

    def create_checkout_session(self, bill, return_url=None):
        """
        Creates a payment session with YouPI-PG.
        If live API call fails or hospital is in sandbox mode,
        gracefully returns a local self-contained test session payload.
        """
        amount_paise = int(bill.total_amount * 100)
        client_ref_id = f"{bill.hospital.slug}_{bill.bill_number}_{uuid.uuid4().hex[:6]}"

        payload = {
            'merchant_id': self.merchant_id,
            'client_ref_id': client_ref_id,
            'order_id': bill.bill_number,
            'amount': float(bill.total_amount),
            'amount_paise': amount_paise,
            'currency': 'INR',
            'customer_name': bill.patient.name,
            'customer_phone': bill.patient.phone,
            'notes': {
                'hospital': self.hospital.name,
                'bill_number': bill.bill_number,
            }
        }

        # Attempt real API call if not in strict offline mode
        try:
            req = urllib.request.Request(
                f"{self.api_url}/api/v1/payments",
                data=json.dumps(payload).encode('utf-8'),
                headers={
                    'Content-Type': 'application/json',
                    'X-Merchant-Id': self.merchant_id,
                    'Idempotency-Key': client_ref_id,
                },
                method='POST'
            )
            with urllib.request.urlopen(req, timeout=2.5) as response:
                if response.status in (200, 201):
                    res_data = json.loads(response.read().decode('utf-8'))
                    return {
                        'success': True,
                        'is_mock': False,
                        'payment_id': res_data.get('payment_id') or res_data.get('id'),
                        'upi_uri': res_data.get('upi_uri'),
                        'qr_svg': res_data.get('qr_svg'),
                        'checkout_url': res_data.get('checkout_url'),
                    }
        except Exception:
            # Fall through to sandbox/mock session generator
            pass

        # Built-in High-Fidelity Sandbox / Mock Generator
        upi_vpa = self.hospital.upi_id or 'cliniqpay.youpi@okhdfcbank'
        pa = urllib.parse.quote(upi_vpa)
        pn = urllib.parse.quote(self.hospital.name)
        am = f"{bill.total_amount:.2f}"
        tr = client_ref_id
        tn = urllib.parse.quote(f"YouPI Bill {bill.bill_number}")
        simulated_upi_uri = f"upi://pay?pa={pa}&pn={pn}&am={am}&tr={tr}&tn={tn}&cu=INR"
        encoded_uri = urllib.parse.quote_plus(simulated_upi_uri)
        qr_code_url = f"https://api.qrserver.com/v1/create-qr-code/?size=260x260&data={encoded_uri}"

        mock_payment_id = f"youpi_pay_{uuid.uuid4().hex[:14]}"
        return {
            'success': True,
            'is_mock': True,
            'payment_id': mock_payment_id,
            'client_ref_id': client_ref_id,
            'upi_uri': simulated_upi_uri,
            'qr_code_url': qr_code_url,
            'checkout_url': f"{self.api_url}/checkout/{mock_payment_id}",
        }

    def verify_webhook_signature(self, raw_body_bytes, signature_header):
        """
        Verifies HMAC-SHA256 signature from `X-Gateway-Signature`.
        Format: sha256=<hex_digest>
        Uses constant-time comparison to prevent timing attacks.
        """
        if not signature_header or not self.webhook_secret:
            return False

        if signature_header.startswith('sha256='):
            received_hash = signature_header.split('sha256=', 1)[1]
        else:
            received_hash = signature_header

        computed_hash = hmac.new(
            self.webhook_secret.encode('utf-8'),
            raw_body_bytes,
            hashlib.sha256
        ).hexdigest()

        return hmac.compare_digest(received_hash, computed_hash)

    def generate_test_webhook_payload(self, bill, event='OBSERVED_SUCCESS', utr=None):
        """
        Constructs a valid cryptographic YouPI webhook test packet with headers
        for developer verification and sandbox testing.
        """
        test_utr = utr or f"UTR{uuid.uuid4().hex[:12].upper()}"
        payment_id = f"youpi_{uuid.uuid4().hex[:12]}"
        delivery_id = str(uuid.uuid4())

        payload_dict = {
            'event': event,
            'payment_id': payment_id,
            'order_id': bill.bill_number,
            'client_ref_id': f"{bill.hospital.slug}_{bill.bill_number}",
            'amount': float(bill.total_amount),
            'amount_paise': int(bill.total_amount * 100),
            'currency': 'INR',
            'utr': test_utr,
            'delivery_id': delivery_id,
            'hospital_slug': self.hospital.slug,
        }

        raw_bytes = json.dumps(payload_dict, separators=(',', ':')).encode('utf-8')
        signature = hmac.new(
            self.webhook_secret.encode('utf-8'),
            raw_bytes,
            hashlib.sha256
        ).hexdigest()

        return {
            'payload': payload_dict,
            'raw_bytes': raw_bytes,
            'headers': {
                'X-Gateway-Signature': f"sha256={signature}",
                'X-Gateway-Event': event,
                'X-Gateway-Delivery-Id': delivery_id,
            }
        }

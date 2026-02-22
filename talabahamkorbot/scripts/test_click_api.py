import requests
import hashlib
import time

BASE_URL = "http://127.0.0.1:8000/api/v1/payment/click"
SECRET_KEY = "TEST_SECRET_KEY"

def generate_sign(trans_id, service_id, secret, merchant_trans_id, amount, action, sign_time, prep_id=None):
    amount_str = f"{float(amount):.2f}".replace(".00", "") if float(amount).is_integer() else f"{float(amount):.2f}"
    if prep_id is not None:
        raw = f"{trans_id}{service_id}{secret}{merchant_trans_id}{prep_id}{amount_str}{action}{sign_time}"
    else:
        raw = f"{trans_id}{service_id}{secret}{merchant_trans_id}{amount_str}{action}{sign_time}"
    return hashlib.md5(raw.encode('utf-8')).hexdigest()

def test_click_flow():
    click_trans_id = 123456789
    service_id = 1
    click_paydoc_id = 987654321
    merchant_trans_id = "ORDER-1001"
    amount = 50000.00
    sign_time = time.strftime("%Y-%m-%d %H:%M:%S")

    # 1. PREPARE
    action = 0
    sign_string = generate_sign(click_trans_id, service_id, SECRET_KEY, merchant_trans_id, amount, action, sign_time)
    
    prep_data = {
        "click_trans_id": click_trans_id,
        "service_id": service_id,
        "click_paydoc_id": click_paydoc_id,
        "merchant_trans_id": merchant_trans_id,
        "amount": amount,
        "action": action,
        "error": 0,
        "error_note": "",
        "sign_time": sign_time,
        "sign_string": sign_string
    }
    
    print("--- Sending Prepare ---")
    resp1 = requests.post(f"{BASE_URL}/prepare", data=prep_data)
    print(resp1.status_code)
    try:
        prep_json = resp1.json()
        print(prep_json)
    except:
        print(resp1.text)
        return

    if prep_json.get("error") != 0:
        print("Prepare failed. Stopping.")
        return
        
    merchant_prepare_id = prep_json.get("merchant_prepare_id")

    # 2. COMPLETE
    action = 1
    sign_time = time.strftime("%Y-%m-%d %H:%M:%S")
    sign_string = generate_sign(click_trans_id, service_id, SECRET_KEY, merchant_trans_id, amount, action, sign_time, merchant_prepare_id)
    
    comp_data = {
        "click_trans_id": click_trans_id,
        "service_id": service_id,
        "click_paydoc_id": click_paydoc_id,
        "merchant_trans_id": merchant_trans_id,
        "merchant_prepare_id": merchant_prepare_id,
        "amount": amount,
        "action": action,
        "error": 0,
        "error_note": "",
        "sign_time": sign_time,
        "sign_string": sign_string
    }
    
    print("\n--- Sending Complete ---")
    resp2 = requests.post(f"{BASE_URL}/complete", data=comp_data)
    print(resp2.status_code)
    try:
        print(resp2.json())
    except:
        print(resp2.text)

if __name__ == "__main__":
    test_click_flow()

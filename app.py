from flask import Flask, request, jsonify
import requests

app = Flask(__name__)

# Infobip API konfiguracija
INFOBIP_CONFIG = {
    'api_key': 'YOUR_INFOBIP_API_KEY',  # Zamijeni sa pravim API ključem
    'base_url': 'https://api.infobip.com',
    'sender': 'InfoSMS'  # Naziv pošiljatelja (do 11 znakova)
}

def send_sms_infobip(phone_number, message):
    """
    Šalje SMS poruku preko Infobip API-ja
    
    Args:
        phone_number (str): Broj telefona u E.164 formatu (npr. +385981234567)
        message (str): Tekst poruke
    
    Returns:
        dict: Rezultat slanja sa statusom i podacima
    """
    url = f"{INFOBIP_CONFIG['base_url']}/sms/2/text/advanced"
    
    headers = {
        'Authorization': f"App {INFOBIP_CONFIG['api_key']}",
        'Content-Type': 'application/json',
        'Accept': 'application/json'
    }
    
    payload = {
        'messages': [
            {
                'from': INFOBIP_CONFIG['sender'],
                'destinations': [
                    {
                        'to': phone_number
                    }
                ],
                'text': message
            }
        ]
    }
    
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=10)
        response.raise_for_status()
        
        result = response.json()
        return {
            'success': True,
            'message': 'SMS poslan uspješno',
            'data': result
        }
        
    except requests.exceptions.HTTPError as e:
        error_data = e.response.json() if e.response else {}
        return {
            'success': False,
            'error': f"HTTP greška: {e.response.status_code}",
            'details': error_data
        }
        
    except requests.exceptions.RequestException as e:
        return {
            'success': False,
            'error': f"Greška pri slanju: {str(e)}"
        }

@app.route('/send-sms', methods=['POST'])
def send_sms():
    """
    API endpoint za slanje SMS-a
    
    Očekuje JSON:
    {
        "phoneNumber": "+385993652688",
        "message": "Adria Connect to the sky!"
    }
    """
    data = request.get_json()
    
    # Validacija inputa
    if not data:
        return jsonify({
            'success': False,
            'error': 'JSON tijelo zahtjeva je obavezno'
        }), 400
    
    phone_number = data.get('phoneNumber')
    message = data.get('message')
    
    if not phone_number:
        return jsonify({
            'success': False,
            'error': 'phoneNumber je obavezan'
        }), 400
    
    if not message:
        return jsonify({
            'success': False,
            'error': 'message je obavezan'
        }), 400
    
    # Validacija formata broja
    if not phone_number.startswith('+'):
        return jsonify({
            'success': False,
            'error': 'Broj telefona mora počinjati sa + (E.164 format)'
        }), 400
    
    # Slanje SMS-a
    result = send_sms_infobip(phone_number, message)
    
    if result['success']:
        return jsonify(result), 200
    else:
        return jsonify(result), 500

@app.route('/send-bulk-sms', methods=['POST'])
def send_bulk_sms():
    """
    API endpoint za slanje SMS-a na više brojeva odjednom
    
    Očekuje JSON:
    {
        "phoneNumbers": ["+385981234567", "+385981234568"],
        "message": "Vaša poruka ovdje"
    }
    """
    data = request.get_json()
    
    if not data:
        return jsonify({
            'success': False,
            'error': 'JSON tijelo zahtjeva je obavezno'
        }), 400
    
    phone_numbers = data.get('phoneNumbers', [])
    message = data.get('message')
    
    if not phone_numbers or not isinstance(phone_numbers, list):
        return jsonify({
            'success': False,
            'error': 'phoneNumbers mora biti lista brojeva'
        }), 400
    
    if not message:
        return jsonify({
            'success': False,
            'error': 'message je obavezan'
        }), 400
    
    # Slanje na sve brojeve
    results = []
    for phone in phone_numbers:
        result = send_sms_infobip(phone, message)
        results.append({
            'phoneNumber': phone,
            'success': result['success'],
            'error': result.get('error')
        })
    
    successful = sum(1 for r in results if r['success'])
    failed = len(results) - successful
    
    return jsonify({
        'success': True,
        'total': len(results),
        'successful': successful,
        'failed': failed,
        'results': results
    }), 200

@app.route('/health', methods=['GET'])
def health():
    """Provjera statusa servisa"""
    return jsonify({
        'status': 'OK',
        'service': 'Infobip SMS Service'
    }), 200

if __name__ == '__main__':
    print("=" * 50)
    print("Infobip SMS Servis pokrenut!")
    print("=" * 50)
    print("\nDostupni endpointi:")
    print("  POST /send-sms        - Pošalji SMS na jedan broj")
    print("  POST /send-bulk-sms   - Pošalji SMS na više brojeva")
    print("  GET  /health          - Provjera statusa\n")
    print("Server se pokreće na http://localhost:5000")
    print("=" * 50)
    
    app.run(host='0.0.0.0', port=5000, debug=True)

import json
import hashlib
import requests
from datetime import date, datetime
from time import sleep

today = date.today().strftime(r"%d-%m-%Y")
beneficiaries = [
]
my_loc = (8, 76)

# Urls
generate_otp_url = "https://cdn-api.co-vin.in/api/v2/auth/generateMobileOTP"
validate_otp_url = "https://cdn-api.co-vin.in/api/v2/auth/validateMobileOtp"
search_url = f"https://cdn-api.co-vin.in/api/v2/appointment/sessions/calendarByDistrict?district_id=296&date={today}&vaccine=COVISHIELD"
schedule_url = "https://cdn-api.co-vin.in/api/v2/appointment/schedule"
logout_url = "https://cdn-api.co-vin.in/api/v2/auth/logout"

generate_otp_data = json.dumps({
    "mobile": "",
    "secret":"U2FsdGVkX19AIlq3zCNBIw6h+/47Z18FRuHS1kbD6Wb7z9PCv8X5q/5iicDzFRosGYFi6sVUBxsChWPEh2hHng=="
})


gotp_resp = requests.post(generate_otp_url, data=generate_otp_data)
tnx_id = gotp_resp.json()["txnId"]
otp_num = input("Enter OTP from mobile: ")
otp_sha = hashlib.sha256(otp_num.encode()).hexdigest()

validate_otp_data = json.dumps({
    "txnId": tnx_id,
    "otp": otp_sha
})

votp_resp = requests.post(validate_otp_url, data=validate_otp_data)
token = votp_resp.json()["token"]

auth_header = {
    "authorization": f"Bearer {token}"
}

def book_now():
    search_resp = requests.get(search_url, headers=auth_header)
    data = search_resp.json()

    for i in data["centers"]:
        if i["fee_type"] == "Free" and i["block_name"] == "Thiruvananthapuram":
            # distance = sqrt((x1-x2)^2 + (y1-y2)^2)
            dist = ((my_loc[0] - i["lat"]) ** 2 + (my_loc[1] - i["long"]) ** 2) ** 0.5 * 111.321
            for j in i["sessions"]:
                if (j["vaccine"] == "COVISHIELD" and
                        (j["min_age_limit"] == 18 or j["allow_all_age"] is True) and
                        j["available_capacity_dose2"] != 0):
                    print("Name: ", i["name"])
                    print("Address: ", i["address"])
                    print("Distance: ", dist)
                    print("Slots: ", j["slots"][0])
                    print("Availability: ", j["available_capacity_dose2"])
                    schedule_data = json.dumps({
                        "dose": 2,
                        "session_id": j["session_id"],
                        "slot": j["slots"][0],
                        "beneficiaries": beneficiaries
                    })
                    schedule_resp = requests.post(schedule_url, data=schedule_data)
                    if schedule_resp.status_code == 409:
                        print("Schedule full now\n")
                        continue
                    if schedule_resp.status_code == 200:
                        print("Booked Successfully\n")
                        exit(0)

book_now()

try:
    for _i in range(0, 180):
        print(f"Try time: {datetime.now()}")
        book_now()
        print("No slot found! Will try in 30 seconds")
        sleep(30)
except (KeyboardInterrupt, KeyError, IndexError) as err:
    print(err)
finally:
    print("Exiting now")

# logout
logout_resp = requests.get(logout_url, headers=auth_header)
print(logout_resp.status_code)

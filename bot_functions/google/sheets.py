import gspread
from gspread_formatting import *
import time
import sys
if "/bot_functions" not in sys.path:
    sys.path.append("/bot_functions")
from keys_and_codes import gcreds

class Cell:
    def __init__(self, r, c, v):
        self.col = c
        self.row = r
        self.value = v
        print(v)

def create_spreadsheet(spreadsheet_name):
    gc = gspread.service_account(filename=gcreds)
    sh = gc.create(spreadsheet_name)
    sh.share(None, 'anyone', 'writer', notify=True, email_message=None, with_link=True)
    worksheet = sh.worksheet('Sheet1')
    worksheet.update_title('Master')
    return sh.url,worksheet

def load_spreadsheet(spreadsheet_url,worksheet_name='Master'):
    gc = gspread.service_account(filename=gcreds)
    sh = gc.open_by_url(spreadsheet_url)
    worksheet = sh.worksheet(worksheet_name)
    return sh.url,worksheet

def load_spreadsheet_as_dict_list(spreadsheet_url,worksheet_name='Master',header_row=1):
    url,worksheet = load_spreadsheet(spreadsheet_url,worksheet_name)
    all_values = worksheet.get_all_values()
    keys_raw = all_values[header_row-1]
    keys=[]
    dicts = []

    for key in keys_raw:
        keys.append(key.replace(' ','_').lower())

    for row in all_values[header_row:]:
        row_dict={}
        for key,value in zip(keys,row):
            print(f"{key}: {value}")
            row_dict[key]=value
        dicts.append(row_dict)
    return dicts

def deploy_template(template_type,sheet_url,deploy_template):
    if 'bulk_nft_import' == template_type.lower():
        template_url = 'https://docs.google.com/spreadsheets/d/1rssbmGATl7BtucazEFOK4iVRANshTE9bbMI80eaLkdQ'
    elif 'nft' in template_type.lower():
        template_url = 'https://docs.google.com/spreadsheets/d/17MnI8C6enBeGh2PWIruS1H-YA0Wqq0v7g-nHvHMMvp8'
    print(f"Deploying {template_type} template to {sheet_url}")
    gc = gspread.service_account(filename=gcreds)
    sh = gc.open_by_url(sheet_url)
    template_sh = gc.open_by_url(template_url)
    template_sh.worksheet('Master').copy_to(sh.id)
    worksheet = sh.worksheet('Master')
    sh.del_worksheet(worksheet)
    worksheet = sh.worksheet('Copy of Master')
    worksheet.update_title('Master')
    if 'bulk_nft_import' == template_type.lower():
        update_cell_list=[]
        update_cell_list.append(Cell(1,  4, deploy_template))
    return sh.url,worksheet

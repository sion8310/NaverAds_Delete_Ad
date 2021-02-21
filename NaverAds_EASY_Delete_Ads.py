import time
import random
import requests
import urllib.parse
import json
import base64
import hmac
import hashlib
import jsonpickle
import pandas as pd
import numpy as np
from prettytable import PrettyTable


pd.set_option('display.max_rows', 1000)
pd.set_option('display.max_columns', 1000)
pd.set_option('display.width', 1000)


# pd.set_option('display.colheader_justify', 'right')

# Naver Signature
class Signature:
    @staticmethod
    def generate(timestamp, method, uri, secret_key):
        message = "{}.{}.{}".format(timestamp, method, uri)
        hash = hmac.new(bytes(secret_key, "utf-8"), bytes(message, "utf-8"), hashlib.sha256)

        hash.hexdigest()
        return base64.b64encode(hash.digest())


def get_header(method, uri, api_key, secret_key, customer_id):
    timestamp = str(round(time.time() * 1000))
    signature = Signature.generate(timestamp, method, uri, secret_key)
    return {'Content-Type': 'application/json; charset=UTF-8', 'X-Timestamp': timestamp, 'X-API-KEY': api_key,
            'X-Customer': str(CUSTOMER_ID), 'X-Signature': signature}


print("네이버 검색광고 광고소재 자동 삭제 프로그램")


BASE_URL = 'https://api.naver.com'
print("API 접속을 위한 정보는 네이버 검색광고 도구 탭 -> API 사용관리 버튼을 누르시면 됩니다.")
print("\n")
print("\n")
API_KEY = str(input("API KEY [엑세스라이선스] 값을 입력해주세요.\n")).strip()
print("\n")
SECRET_KEY = str(input("API SECRET [비밀키] 값을 입력해주세요.\n")).strip()
print("\n")
CUSTOMER_ID = str(input("CUSTOMER ID값을 입력해주세요.\n")).strip()



def print_df(df):
    if isinstance(df, pd.pandas.core.frame.DataFrame):
        table = PrettyTable([''] + list(df.columns))

        for row in df.itertuples():
            table.add_row(row)

        print(str(table))
    else:
        print(df)

    print("\n")


def account_info(pro):
    #####################################################################################################
    # 캠페인 정보 빼내고
    print("캠페인 정보를 수집하고 있습니다.")

    uri = '/ncc/campaigns'
    method = 'GET'
    r = requests.get(BASE_URL + uri, headers=get_header(method, uri, API_KEY, SECRET_KEY, CUSTOMER_ID))
    data = r.json()

    campaign_result = pd.read_json(json.dumps(data))
    try:
        campaign_result = campaign_result[['nccCampaignId', 'name']]
        campaign_result.columns = ['nccCampaignId', 'Campaign_Name']
    except:
        campaign_result = pd.DataFrame(columns=['nccCampaignId', 'Campaign_Name'])
    print("캠페인 정보를 수집 완료했습니다.")

    #####################################################################################################
    # 광고그룹 정보 빼내고
    print("광고그룹 정보를 수집하고 있습니다.")

    uri = '/ncc/adgroups'
    method = 'GET'
    r = requests.get(BASE_URL + uri, headers=get_header(method, uri, API_KEY, SECRET_KEY, CUSTOMER_ID))
    data = r.json()

    adgroup_result = pd.read_json(json.dumps(data))

    try:
        adgroup_result = adgroup_result[['nccAdgroupId', 'name', 'nccCampaignId']]
        adgroup_result.columns = ['nccAdgroupId', 'AdGroup_Name', 'nccCampaignId']
    except:
        adgroup_result = pd.DataFrame(columns=['nccAdgroupId', 'AdGroup_Name', 'nccCampaignId'])

    print("광고그룹 정보를 수집 완료했습니다.")

    #####################################################################################################
    print("광고소재 정보를 수집하고 있습니다.")

    uri = '/ncc/ads'
    method = 'GET'
    AD_result = pd.DataFrame()

    for adgroup_id in adgroup_result['nccAdgroupId'].values.tolist():
        # print(adgroup_id)
        r = requests.get(BASE_URL + uri, params={'nccAdgroupId': adgroup_id},
                         headers=get_header(method, uri, API_KEY, SECRET_KEY, CUSTOMER_ID))
        data = r.json()
        result = pd.read_json(json.dumps(data))
        AD_result = pd.concat([AD_result, result], sort=True)

    AD_result = AD_result[['nccAdId', 'nccAdgroupId']]
    print("광고소재 정보를 수집 완료했습니다.")
    #########################################################################################################
    # 필요 데이터만 뽑아내보자.

    # 이건 AdGroup 전체 삭제 버전
    if pro == '1':
        final_df = pd.merge(AD_result, adgroup_result, on='nccAdgroupId')
        final_df = pd.merge(final_df, campaign_result, on='nccCampaignId')
        return final_df

    if pro == '2':
        final_df2 = pd.merge(adgroup_result, campaign_result, on='nccCampaignId')
        grouped = AD_result.groupby(AD_result['nccAdgroupId']).count()
        final_df2 = pd.merge(final_df2, grouped, on='nccAdgroupId')
        final_df2.columns = ['광고그룹ID', '광고그룹_이름', '캠페인ID', '캠페인_이름', '등록된_소재_수']
        final_df2 = final_df2[['캠페인_이름', '캠페인ID', '광고그룹_이름', '광고그룹ID', '등록된_소재_수']]
        final_df2.index += 1
        return final_df2

    #########################################################################################################


def excel_delete():
    final_df = account_info(str(1))
    print("\n\n\n")
    file_name = str(input("확장자명을 제외한 엑셀 파일 이름을 쳐주세요.\n"))
    file_name = file_name + ".xlsx"

    flag = True
    while (flag):
        try:
            exl_data = pd.read_excel(file_name)
            print("데이터를 성공적으로 불러왔습니다.")
            flag = False
        except:
            print("파일 이름이 잘못됬습니다. 다시 한번 입력해주세요.")
            file_name = str(input("확장자명을 제외한 엑셀 파일 이름을 쳐주세요.\n"))
            file_name = file_name + ".xlsx"

    exl_data = pd.read_excel(file_name)
    print("데이터를 성공적으로 불러왔습니다.")

    print("업로드 하기전에 확인 작업을 거치겠습니다.")

    df = pd.merge(exl_data, final_df, on='nccAdId')
    print("\n삭제하고자 하는 소재 리스트 및 정보:")
    print_df(df)

    continue_decision = str(input("\n\n 위의 내용이 맞습니까? 맞다면 (1)번을 틀리면 (2)번을 눌러주세요.\n"))
    if continue_decision == '2':
        exit(1)

    ####################################################################################################
    # 삭제 시작

    print("삭제 작업 시작하겠습니다.")

    deleted_ad_ID = df['nccAdId']
    method = 'DELETE'
    uri = '/ncc/ads'
    for ids in deleted_ad_ID.values.tolist():
        uri = '/ncc/ads/' + ids
        r = requests.delete(BASE_URL + uri, headers=get_header(method, uri, API_KEY, SECRET_KEY, CUSTOMER_ID))

    print("삭제 작업 완료했습니다.")

    time.sleep(1)
    print('3초 후에 프로그램이 종료됩니다.')
    time.sleep(3)

##############################################################################################################


def Adgroup_Delete():
    flag = True
    while flag == True:
        #데이터 출력
        final_df2 = account_info(str(2))
        final_df2.columns = ['Campaign_Name', 'Campaign_ID', 'AdGroup_Name', 'AdGroup_ID', 'Num_Of_Ads']


        print("\n\n\n")
        print_df(final_df2)
        print("\n\n\n")

        id_idx = str(input("삭제하고자 하는 광고그룹 Row Number을 적어주세요. 프로그램 종료는 00을 입력해주세요\n"))
        if id_idx == '00':
            print("프로그램 종료하겠습니다.")
            break

        print("삭제 전, 광고그룹의 정보를 꼭 확인해주세요.\n")
        print(final_df2.loc[int(id_idx)])
        decision = str(input("\n\n 소재 전체 삭제를 원하는 광고그룹의 정보가 맞습니까?\n맞으면 (1), 틀리면 (2)를 입력해주세요"))

        #여기서부터 Decision 시작.
        if decision == '1':
            #일단 해당 AdGroup안에 있는 ADs들을 가져오자.
            delete_adgroup_id = final_df2.loc[int(id_idx)]['AdGroup_ID']
            print("\n\n\n")
            print(delete_adgroup_id)
            uri = '/ncc/ads'
            method = 'GET'
            r = requests.get(BASE_URL + uri, params={'nccAdgroupId': delete_adgroup_id},
                             headers=get_header(method, uri, API_KEY, SECRET_KEY, CUSTOMER_ID))
            data = r.json()
            result = pd.read_json(json.dumps(data))

            #가져온 것에서 Ads ID만 빼오기
            deleted_ad_ID = result['nccAdId']
            print(deleted_ad_ID)
            #삭제 시작
            method = 'DELETE'
            for ids in deleted_ad_ID.values.tolist():
                uri = '/ncc/ads/' + ids
                r = requests.delete(BASE_URL + uri, headers = get_header(method, uri, API_KEY, SECRET_KEY, CUSTOMER_ID))
            print("삭제 완료 되었습니다.")
            print("다시 메뉴로 돌아가겠습니다.")
            print("\n\n\n")
#########################################################################################################################

program_decision = str(input("삭제 방법을 결정해주세요.\n(1)엑셀 일괄 처리\n(2)광고그룹 일괄 처리\n"))

if program_decision == '1':
    excel_delete()
if program_decision == '2':
    Adgroup_Delete()


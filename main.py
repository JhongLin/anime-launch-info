import json
import requests
from datetime import datetime, timedelta

from playwright.sync_api import sync_playwright
from playwright.sync_api._generated import Browser, ElementHandle, Page

WEBHOOK_URL: str = 'your_webhook_url'
WEEK_DAY_MAPPING = {
    0: '月曜',
    1: '火曜',
    2: '水曜',
    3: '木曜',
    4: '金曜',
    5: '土曜',
    6: '日曜',
}


def send_discord_message(
    webhook_url: str,
    dict_data: dict,
) -> None:
    headers: dict = {
        'Content-Type': 'application/json'
    }
    response: requests.Response = requests.post(webhook_url, data=json.dumps(dict_data), headers=headers)

    if response.status_code == 204:  #  The HTTP status code 204 No Content success
        print('Message sent successfully.')

    else:
        print(f'Failed to send message. Response: {response.text}')


def main() -> None:
    now: datetime = datetime.now()
    message_list: list[str] = []

    with sync_playwright() as p:
        # 1. Launch a new browser and access to the site for scraping information
        browser: Browser = p.chromium.launch()
        page: Page = browser.new_page()
        page.goto('https://www.posite-c.com/anime/weekly/', wait_until='domcontentloaded')

        # 2. Obtain the main table of information
        tbody: ElementHandle = page.query_selector('#ani_b > tbody')

        if not tbody:
            browser.close()
            return

        rows: list[ElementHandle] = tbody.query_selector_all('tr')
        rows_number: int = len(rows)
        i: int = 1  # The first line 0 is the column header

        # 3. Start parsing information on every anime
        while i < rows_number:
            tr_list: list[ElementHandle] = [rows[i]]
            j: int = i + 1

            # 3.1. Collect every row of different launch information on the same anime
            while j < rows_number:

                if rows[j].query_selector('td.b_td_title'):
                    break

                tr_list.append(rows[j])
                j += 1

            is_new: bool = True
            launch_period: list[str] = []
            fastest_date: str = ''

            for tr in tr_list:

                # 3.2. Check whether this anime is a relaunch anime
                if tr.query_selector('td.slct.bcs > div.bcs_re'):
                    is_new = False
                    break

                # 3.3. Check whether this anime is not a new launch anime
                if not tr.query_selector('td.slct.bcs > div.bcs_new'):
                    is_new = False
                    break

                # 3.4. Obtain the information of launch date and launch period
                if fastest_date == '' or launch_period == []:

                    if tr.query_selector('td.slct.b_td_info > div.o_a') or len(tr_list) == 1:
                        td_slct_list: list[ElementHandle] = tr.query_selector_all('td.slct')
                        fastest_date = td_slct_list[2].text_content()
                        launch_period = td_slct_list[5].text_content().split('～')

            if is_new:

                # 3.5. Integrate the message with the parsed information
                if fastest_date[:2] == WEEK_DAY_MAPPING[now.weekday()]:
                    title_link_element: ElementHandle = rows[i].query_selector('td.b_td_title > a')
                    title_text: str = title_link_element.text_content()
                    title_link: str = title_link_element.get_attribute('href')
                    time_slot: str = fastest_date[2:]
                    episode_order: int = (now.date() - datetime.strptime(launch_period[0], '%Y/%m/%d').date()) // timedelta(weeks=1) + 1
                    is_end: bool = False

                    if launch_period[1]:
                        is_end = datetime.strptime(launch_period[1], '%Y/%m/%d').date() == now.date()

                    message: str = f'[{title_text}]({title_link}) IN ORDER {episode_order} ON TODAY\'S {time_slot}'

                    if is_end:
                        message += ' (THE END)'

                    message_list.append(message)

            i = j

        browser.close()

    # 4. Send message via Discord Webhook
    combined_message: str = '\n\n'.join(message_list)
    send_discord_message(WEBHOOK_URL, {'content': combined_message})


if __name__ == '__main__':
    main()

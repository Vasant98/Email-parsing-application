# -*- coding: utf-8 -*-
"""
Created on Thu May 12 11:01:05 2022

@author: Wang Sheng
"""
import requests
from urllib.parse import urlparse, urljoin
from bs4 import BeautifulSoup
import pandas as pd
import re
import PySimpleGUI as sg
import time
import os
#%% Initialisation
# initialize the set of links (unique links)
internal_urls = set()
external_urls = set()
emails = set()

total_urls_visited = 0
total_url = 0
requests_session = requests.Session()

EMAIL_REGEX = r"[a-z0-9\.\-+_]+@[a-z0-9\.\-+_]+\.[a-z]+"
forbidden_keys = ['google', 'facebook', 'instagram', 'tel:', 'mailto:', '.jpg', '.pdf', '.png']
output_mail = ""
print = sg.Print

#%% Functions
def is_valid(url):
    """
    Checks whether `url` is a valid URL.
    """
    parsed = urlparse(url)
    return bool(parsed.netloc) and bool(parsed.scheme)

def is_mailto(href):
    global output_mail
    if href.startswith('mailto://'):
        x = re.search(EMAIL_REGEX, href)
        output_mail = x.group(0)
        match = True
    else:
        match = False
    
    return bool(match), output_mail

def save_file(emails, file_name):
    dfope = pd.DataFrame(emails, columns=["Email"])

    output_list = []
    for i in dfope['Email'].unique():
        # print(i)
        output_list.append(i)

    output_txt = "; ".join(output_list)
    
    output_path = os.path.normpath(os.path.expanduser(file_name))
    with open(output_path, 'w', encoding="utf-8") as f:
        f.write(output_txt)
        
def get_all_website_links(url):
    """
    Returns all URLs that is found on `url` in which it belongs to the same website
    """
    # all URLs of `url`
    urls = set()
    # domain name of the URL without the protocol
    domain_name = urlparse(url).netloc
    soup = BeautifulSoup(requests_session.get(url).content, "lxml")
    
    # Extract email html
    # new_emails = set(re.findall(EMAIL_REGEX, response.text, re.I))
    # for email in new_emails.copy():
    #     if email_domain not in email:
    #         new_emails.remove(email)
    # if new_emails != None:
    #     print(f"[@] {len(new_emails)} more emails were found", text_color='white', background_color='blue')  
    # emails.update(new_emails)
    # new_emails = set()

    for a_tag in soup.findAll("a"):
        href = a_tag.attrs.get("href")

        if href == "" or href is None:
            # href empty tag
            continue
        # join the URL if it's relative (not absolute link)
        href = urljoin(url, href)
        parsed_href = urlparse(href)
        # remove URL GET parameters, URL fragments, etc.
        href = parsed_href.scheme + "://" + parsed_href.netloc + parsed_href.path
        if not is_valid(href):
            # not a valid URL
            continue
        if is_mailto(href)[0]:
            # select those href that starts with mailto://
            emails.add(is_mailto(href)[1])
            
            print(f"[@] Found email: {is_mailto(href)[1]}", text_color='white', background_color='blue')
            save_file(emails, filename)
            continue
        
        if href in internal_urls:
            # already in the set
            continue
        if domain_name not in href:
            # external link
            if href not in external_urls:
                print(f"[!] External link: {href}")
                external_urls.add(href)
            continue

        print(f"[*] Internal link: {href}", text_color='white', background_color='green' )
        urls.add(href)
        internal_urls.add(href)

    return urls

def crawl(url, max_urls, total_url_specified):
    """
    Crawls a web page and extracts all links.
    You'll find all links in `external_urls` and `internal_urls` global set variables.
    params:
        max_urls (int): number of max urls to crawl, default is 30.
    """
    global total_urls_visited
    global total_url
    total_urls_visited += 1
    total_url += 1

    print(f"[*] Crawling: {url}", text_color='black', background_color='yellow')
    links = get_all_website_links(url)
    for link in links:
        # skip = False
        # for key in forbidden_keys:
        #     if key in link:
        #         print(link, 'caught!!!!')
        #         skip = True
        #         break
        # if skip:
        #     print('reset')
        #     break
            
        if total_urls_visited > max_urls:
            total_urls_visited = 0
            break
        try:
            crawl(link, max_urls=max_urls)
            if total_url == total_url_specified:
                break
        except:
            requests_session = requests.Session()
            continue
        
        
def run(target_website, max_urls, email_domain, total_url_specified):
    global filename
    timer_start = time.perf_counter()
    crawl(target_website, max_urls, total_url_specified)
    filename = f'email__{email_domain}__{time.strftime("%Y%m%d")}__{time.strftime("%H%M%S")}.txt'
    print("[+] Total Internal links:", len(internal_urls))
    print("[+] Total External links:", len(external_urls))
    print("[+] Total URLs:", len(external_urls) + len(internal_urls))
    print("[+] Total emails:", len(emails))
    
    df = pd.DataFrame(internal_urls, columns=["url"])

    requests_session_2 = requests.Session()
    # looping = True

    
    # while looping:
    for ind in df.index:
        try:
            url = df['url'][ind]
            print(f"[*] Crawling {str(ind)}/{df.shape[0]}: {url}", text_color='black', background_color='yellow')
            soup = BeautifulSoup(requests_session_2.get(url).content, 'lxml')
            
            # Extract email html
            # new_emails = set(re.findall(EMAIL_REGEX, response.text, re.I))
            # for email in new_emails.copy():
            #     if email_domain not in email:
            #         new_emails.remove(email)
            # if new_emails != None:
            #     print(f"[@] {len(new_emails)} more emails were found", text_color='white', background_color='blue')  
            # emails.update(new_emails)
            # new_emails = set()
            
            mailtos = soup.select('a[href^=mailto]')
            
            for i in mailtos:
                if i.string != None and str(i.string).__contains__(email_domain) and str(i.string).__contains__('@'):
                    print(f"[@] Found email: {str(i.string)}", text_color='white', background_color='blue')
                    emails.add(i.string)
                    save_file(emails, filename)
                    
            if ind == df.shape[0]:
                break
        except:
            requests_session_2 = requests.Session()
            continue
        
    
    save_file(emails, filename)
    timer_end = time.perf_counter()
    
    print('\n=======================================================')
    print(f'Total email extracted: {len(emails)}')
    print(f'Total site crawled: {len(internal_urls)}')
    print(f'Total time spent: {timer_end - timer_start:0.4f} seconds')
    print('\n=======================================================')
    print('List of emails has been saved in the text file.')

#set the theme for the screen/window
sg.theme("LightPurple")


# class Unbuffered(object):
#     def __init__(self, window):
#         self.window = window
#     def write(self, data):
#         self.window.write_event_value("OUT", data)
#     def writelines(self, datas):
#         self.window.write_event_value("OUT", ''.join(datas))

# frame_layout = [[sg.Multiline("", size=(80, 20), autoscroll=True, key='-output-')]]

# layout = [
#     [sg.Frame("Output console", frame_layout)],
#     [sg.Push(), sg.Button("Print"), sg.Button('Stop')],
# ]
# window = sg.Window("Title", layout, finalize=True)


# Define the window's contents
layout = [[sg.Text('What is your webpage?', size =(20, 1)), sg.InputText('https://chemistry.princeton.edu/faculty', key='-website-')],
          [sg.Text('Email Domain', size =(20, 1)), sg.InputText('princeton.edu', key='-domain-')],
          [sg.Text("Max. url (depth)", size =(20, 1)), sg.InputText('30', key='-url-')],
          [sg.Text("Total max. urls to scrape", size =(20, 1)), sg.InputText('1000', key='-totalurl-')],
          # [sg.Frame("Output console", frame_layout)],
          [sg.Button("Parse")]]
          #[sg.Multiline('', size=(80, 25), font=10, text_color='Blue', key='-output-', reroute_stderr=True, reroute_stdout=True, autoscroll=True, background_color='black',)],]

# Create the window
window = sg.Window('Email Parser', layout)
# old_stdout, old_stderr = sys.stdout, sys.stderr
# sys.stdout = Unbuffered(window)
# sys.stderr = Unbuffered(window)
# printing = False


# Display and interact with the Window using an Event Loop
while True:
    event, values = window.read()
    # See if user wants to quit or window was closed
    if event == sg.WINDOW_CLOSED or event == 'Quit':
        break
    elif event == 'Parse':
        run(target_website=values['-website-'], max_urls=int(values['-url-']), email_domain=values['-domain-']
            , total_url_specified=values['-totalurl-'])
    # elif event == 'Print':
    #     if not printing:
    #         printing = True
    #         threading.Thread(target=print_task(), daemon=True).start()
    # elif event == 'Stop':
    #     sg.Print('eeee')
    #     printing = False
    # elif event == "OUT":
    #     window['-output-'].update(values["OUT"], append=True)
        
        

    # Output a message to the window
    # window['-output-'].update('Hello ' + values['-INPUT-'] + "! Thanks for trying PySimpleGUI")
    # window['-output-'].update(values["-output-"], append=True)

# Finish up by removing from the screen
# printing = False
# sys.stdout, sys.stderr = old_stdout, old_stderr
window.close()

import csv, json

accounts = []
with open(r'C:\Users\henac\Threadsデータ\threads_not_following_back.csv', encoding='utf-8-sig') as f:
    for row in csv.DictReader(f):
        accounts.append({'name': row['アカウント名'], 'url': row['ThreadsURL']})

accounts_json = json.dumps(accounts, ensure_ascii=False)

html_template = open(r'C:\Users\henac\prompt_vault\tool_template.html', encoding='utf-8').read()
html = html_template.replace('__ACCOUNTS_JSON__', accounts_json)

out = r'C:\Users\henac\Threadsデータ\threads_unfollow_tool.html'
with open(out, 'w', encoding='utf-8') as f:
    f.write(html)
print('作成完了:', out)
print('件数:', len(accounts))

import os

# Important Information
BOT_TOKEN = "MTMzNTI4MjYzNjM0MzYwNzMyNg.GIgDZh.fZpj_1LM44P_5zP8yrCICvUavCS7knvtID3nus"
YOUR_GUILD_ID = "529027023742566423"

# Spreadsheet IDs
SPREADSHEET_IDS = {
    'rs3': '1gskxKXMkjvt1gg4085l_XvGESUfcJ5OKQ4o65Hoelgg', # Updated for Test Site
    'osrs': '1Xv2g0WfiO1RRwryQpkqHlHmgiTPhKCYEGGHZLylOhx4' # Updated for Test Site
}

# Discord Role IDs
ROLE_IDS = {
    'osrsbotmod': 1254905498520649759,
    'rs3botmod': 1254905171247628378,
    'discordbotmod': 1256023718350819468,
    'discordmod': 1276350939023802460,
    'giftmod': 1256022889992290325,
    'developermod': 1316294162470928385,
    'donationmod': 1253075609408635005,
    'eventsmod': 1254331324475506759, 
    'newsmod': 1255918920603402361,
    'osrsclanadmin': 1087593148806602753,
    'osrsmember': 1086485830018797650,
    'rolemod': 830968321229979718, 
    'rs3clanadmin': 1317092325427777556,
    'rs3member': 973796251835432970, 
    'ticketmod': 1038651659049504788,
    'guest': 973795302752518235
}

# Discord Channel IDs
CHANNEL_IDS = {
    'controlpanel': 1254909613590052929,
    'debugging': 1272670663177404557,
    'donationscp': 1253075475618861156, 
    'donations': 1253075314578559187, 
    'eventscp': 1254545756950626344, 
    'inactives': 1335331410898194503,
    'logs': 1272670340660592732, 
    'reports': 1019359419328368650,
    'tickets': 1038652013380124672
}

# Discord Webhook URLs
WEBHOOK_URLS = {
    'donations': os.getenv('DONATIONS_WEBHOOK_URL', 'https://discord.com/api/webhooks/1253366996935114752/Z1Re5eyGiSOCp0kplZmd4fUt1zh1DqBWuXMkina2YMkGqLqXXNcQL_uXBVLU-FFSyT6R'),
    'news': os.getenv('NEWS_WEBHOOK_URL', 'https://discord.com/api/webhooks/1215758983479169054/q8H6nX6EYIcOs3_xQvWAlrkERalHrAWlE3rRN7ZYwUcaFmXGp2W-tYl4dgdoVoXcF19D'),
    'eventsosrs': os.getenv('EVENTSOSRS_WEBHOOK_URL', 'https://discord.com/api/webhooks/1187475428449996950/lnbS9jY_X0x6zlRisVeVhzsELOkqmVJ6d6qsabSFBXJzZF3J2_mQTMGBKRQGvK2C_AJb'),
    'eventsrs3': os.getenv('EVENTSRS3_WEBHOOK_URL', 'https://discord.com/api/webhooks/1248470535621574667/3eAkguUZ9xkbrR1W8bypjNgiIojSVjcqmKd2MdNwCGb4oqOm2W6V4UJJBVk_t-5ULzrm'),
    'eventsdiscord': os.getenv('EVENTSDISCORD_WEBHOOK_URL', 'https://discord.com/api/webhooks/1195413025142878279/i6EhstH_3CN5ONpyt01D4ZN1REQTjHHmtA-EZcnHkh1z851tzbiOh4F7n4ZRXesrjYLy')
}

# Discord Copy Message URLs
COPY_MESSAGE = {
    'leaderboardpost': "https://discord.com/channels/529027023742566423/1253075314578559187/1254993793586040882",
    'expenditurespost': "https://discord.com/channels/529027023742566423/1253075314578559187/1254993796593221684",
    'ledgerpost': "https://discord.com/channels/529027023742566423/1253075314578559187/1254993799017398303"
}

# Section for Wise Old Man
WISE_OLD_MAN_CREDENTIALS = {
    'group_id': 6371,
    'verification_code': '510-175-985'
}
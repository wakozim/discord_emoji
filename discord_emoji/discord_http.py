from urllib.parse import quote as _uriquote

import aiohttp


class Route:

    BASE_URL = 'https://discord.com/api/v10'

    def __init__(self, http_method, path, **kwargs):
        self.method = http_method
        url = self.BASE_URL + path
        if kwargs:
            url = url.format_map({k: _uriquote(v) if isinstance(v, str) else v for k, v in kwargs.items()})
        self.url = url


class DiscordAPI:

    def __init__(self, token, *, bot = True):
        self.token: str = f'Bot {token}' if bot else token
        self.bot = bot
        self.user_agent: str = 'Mozilla/5.0 (Linux; U; Linux i664 ; en-US) Gecko/20100101 Firefox/70.0'


    async def request(self, route, *, json = None, data = None):
        url = route.url
        method = route.method

        kwargs = {}
        headers = {}
        headers['Authorization'] = self.token
        headers['User-Agent'] = self.user_agent
        if json:
            headers['Content-Type'] = 'application/json'
            kwargs['json'] = json
        elif data:
            headers['Content-Type'] = ''
            kwargs['data'] = data

        async with aiohttp.ClientSession(headers=headers) as session:
            async with session.request(method, url, **kwargs) as request:
                if request.status != 200:
                    error_text = await request.json()
                    print(f'ERROR {request.status}: Something went wrong: {error_text}')
                    return None
                return await request.json()

    def get_dms(self) -> dict:
       return self.request(Route('GET', '/users/@me/channels'))

    def get_channels(self) -> dict:
        return self.request(Route('GET', ''))

    def get_channel(self, channel_id: int) -> dict:
        return self.request(Route('GET', '', channel_id=channel_id))

    def get_message(self, channel_id: int, message_id: int) -> dict:
        if self.bot:
            return self.request(Route('GET', '/channels/{channel_id}/messages/%s'))
        else:
            return self.request(Route('GET', '/channels/{channel_id}/messages?around={message_id}&limit=1', channel_id=channel_id, message_id=message_id))

    def send_message(self, channel_id: int, content: str) -> dict:
        data = {}
        #data['embed'] = {'type': 'rich', 'title': 'test'}
        data['sticker_ids'] = [984558194019946546]
        return self.request(Route('POST', '/channels/{channel_id}/messages',
                                           channel_id=channel_id),
                                           json=data)

    def get_guilds(self) -> dict:
        return self.request(Route('GET', '/users/@me/guilds'))

    def get_user(self, user_id: int) -> dict:
        return self.request(Route('GET', '/users/{user_id}',
                                         user_id = user_id))

    def get_guild(self, guild_id: int) -> dict:
        return self.request(Route('GET', '/guilds/{guild_id}', guild_id=guild_id))

    def get_guild_stickers(self, guild_id: int) -> dict:
        return self.request(Route('GET', '/guilds/{guild_id}/stickers', guild_id=guild_id))

    def get_guild_emojis(self, guild_id: int) -> dict:
        return self.request(Route('GET', '/guilds/{guild_id}/emojis', guild_id=guild_id))

    def get_current_application(self) -> dict:
        return self.request(Route('GET', '/applications/@me'))

    def get_guild_members(self, guild_id: int) -> dict:
        return self.request(Route('GET', '/guilds/{guild_id}/members', guild_id=guild_id))

    def get_guild_member(self, guild_id: int, member_id: int) -> dict:
        return self.request(Route('GET', '/guilds/{guild_id}/members/{member_id}', guild_id=guild_id, member_id=member_id))

from src.types.TypeClass import TypeClass

# this is effectively just a fancy dictionary
class LinkDetails(TypeClass):
    class PublicData(TypeClass):
        def __init__(self):
            self.steamid: str = None
            self.visibility_state: int = None
            self.profile_state: int = None
            self.sha_digest_avatar: str = None
            self.persona_name: str = None
            self.profile_url: str = None
            self.content_country_restricted: bool = None

    class PrivateData(TypeClass):
        def __init__(self):
            self.persona_state: int = None
            self.persona_state_flags: int = None
            self.time_created: int = None
            self.game_id: str = None 
            self.broadcast_session_id: str = None
            self.last_logoff_time: int = None # these two values are inaccurate and can't be used to calculate session length
            self.last_seen_online: int = None
            self.game_os_type: int = None # https://steamcommunity.com/discussions/forum/7/1631916887498730773/#c1631916887499079077
            self.game_device_type: int = None # is steam deck, and the like
            self.game_device_name: str = None # hostname
            self.rich_presence_kv: str = None
    
    def __init__(self):
        self.public_data = self.PublicData()
        self.private_data = self.PrivateData()

# this isn't using nested classes as product info simply contains WAY too much for me to include here
class ProductInfo(TypeClass):
    def __init__(self):
        self.appid: str = None
        self.common = {}
        self.extended = {}
        self.config = {}
        self.depots = {}
        self.ufs = {}
        self.localization = {}
        self._missing_token: bool = None
        self._change_number: int = None
        self._sha: str = None
        self._size: int = None
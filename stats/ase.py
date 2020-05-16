import struct

ASE_HAS_PLAYER_COUNT = 0x0004
ASE_HAS_MAX_PLAYER_COUNT = 0x0008
ASE_HAS_GAME_NAME = 0x0010
ASE_HAS_SERVER_NAME = 0x0020
ASE_HAS_GAME_MODE = 0x0040
ASE_HAS_MAP_NAME = 0x0080
ASE_HAS_SERVER_VERSION = 0x0100
ASE_HAS_PASSWORDED_FLAG = 0x0200
ASE_HAS_SERIALS_FLAG = 0x0400
ASE_HAS_PLAYER_LIST = 0x0800
ASE_HAS_RESPONDING_FLAG = 0x1000
ASE_HAS_RESTRICTION_FLAGS = 0x2000
ASE_HAS_SEARCH_IGNORE_SECTIONS = 0x4000
ASE_HAS_KEEP_FLAG = 0x8000
ASE_HAS_HTTP_PORT = 0x080000
ASE_HAS_SPECIAL_FLAGS = 0x100000

class MTAServerlist():
    def readInt(self):
        return self.read(">I")

    def readShort(self):
        return self.read(">H")
    def readChar(self):
        return self.read(">B")

    def read(self, format):
        value = struct.unpack_from(format, self.data, self.offset)
        self.offset += struct.calcsize(format)
        return value[0]

    def readString(self):
        strlen = self.readChar()
        string = ""
        for i in range(0, strlen):
            string = string + chr(self.readChar())
        return string

    async def parse(self, data):
        self.data = data
        self.offset = 0
        self.readShort() # skip length (unused)
        self.version = self.readShort()
        self.flags = self.readInt()
        self.sequence = self.readInt()
        self.count = self.readInt()


        self.hasPlayerCount = self.flags & ASE_HAS_PLAYER_COUNT
        self.hasMaxPlayerCount = self.flags & ASE_HAS_MAX_PLAYER_COUNT
        self.hasGameName = self.flags & ASE_HAS_GAME_NAME
        self.hasServerName = self.flags & ASE_HAS_SERVER_NAME
        self.hasGameMode = self.flags & ASE_HAS_GAME_MODE
        self.hasMapName = self.flags & ASE_HAS_MAP_NAME
        self.hasServerVersion = self.flags & ASE_HAS_SERVER_VERSION
        self.hasPasswordedFlag = self.flags & ASE_HAS_PASSWORDED_FLAG
        self.hasSerialsFlag = self.flags & ASE_HAS_SERIALS_FLAG
        self.hasPlayerList = self.flags & ASE_HAS_PLAYER_LIST
        self.hasRespondingFlag = self.flags & ASE_HAS_RESPONDING_FLAG
        self.hasRestrictionFlags = self.flags & ASE_HAS_RESTRICTION_FLAGS
        self.hasSearchIgnoreSections = self.flags & ASE_HAS_SEARCH_IGNORE_SECTIONS
        self.hasKeepFlag = self.flags & ASE_HAS_KEEP_FLAG
        self.hasHttpPort = self.flags & ASE_HAS_HTTP_PORT
        self.hasSpecial = self.flags & ASE_HAS_SPECIAL_FLAGS

        self.servers = []
        for i in range(0, self.count):
            self.servers.append(self.parseServer())

    def parseServer(self):
        server = {}
        entrylength = self.readShort()
        nextoffset = self.offset + entrylength - 2

        ip1 = str(self.readChar())
        ip2 = str(self.readChar())
        ip3 = str(self.readChar())
        ip4 = str(self.readChar())

        server["ip"] = ip4 + "." + ip3 + "." + ip2 + "." + ip1
        server["port"] = self.readShort()
        if self.hasPlayerCount:
            server["players"] = self.readShort()
        if self.hasMaxPlayerCount:
            server["maxplayers"] = self.readShort()
        if self.hasGameName:
            server["gamename"] = self.readString()
        if self.hasServerName:
            server["name"] = self.readString()
        if self.hasGameMode:
            server["gamemode"] = self.readString()
        if self.hasMapName:
            server["map"] = self.readString()
        if self.hasServerVersion:
            server["version"] = self.readString()
        if self.hasPasswordedFlag:
            server["password"] = self.readChar()
        if self.hasSerialsFlag:
            server["serials"] = self.readChar()
        if self.hasPlayerList:
            count = self.readShort()
            server["players"] = []
            for i in range(0, count):
                server["players"].append(self.readString)
        if self.hasRespondingFlag:
            server["responding"] = self.readChar()
        if self.hasRestrictionFlags:
            server["restriction"] = self.readInt()
        if self.hasSearchIgnoreSections:
            num = self.readChar()
            server["searchIgnore"] = []
            for i in range(0, num):
                offset = self.readChar()
                length = self.readChar()
                server["searchIgnore"].append((offset, length))
        if self.hasKeepFlag:
            server["keep"] = self.readChar()
        if self.hasHttpPort:
            server["http"] = self.readShort()
        if self.hasSpecial:
            server["special"] = self.readChar()

        self.offset = nextoffset
        return server

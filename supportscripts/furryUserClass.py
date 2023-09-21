#dictionary for "furryUserClass"
currentfurries = {}

def AddUserToDictionary(id, server_id, webhook_id):
    currentfurries[id] = furryUserClass({server_id, webhook_id})

#class named "furry"
class furryUserClass():
    def __init__(self, sever_webhook_dictionary, chance):
        self.sever_webhook_dictionary = sever_webhook_dictionary
        self.chance = chance

    def Change_Chance(self, new_chance):
        self.chance = new_chance
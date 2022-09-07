from re import sub
from app.Util import debugger


class Message:
    def __init__(self) -> None:
        self.id: str = None
        self.play_id: str = None
        self.reset()
        return None
    
    def reset(self) -> None:
        self.title: str = None
        self.description: str = None
        self.content: str = None
        self.items: str = []
        self.d: str = None
        return None
    
    def sanatize(self, content: any) -> str:
        content = sub(r'[\*_`\n<>]', '', sub(r':.+?: ', '', str(content)))
        return content
    
    def make(self, event: dict) -> None:
        self.reset()
        
        #Check components
        _components = event['components']
        custom_id = None
        if _components != []:
            for component in _components[0]['components']:
                #"label": "Fish Again"
                try:
                    if component['label'] == 'Fish Again':
                        custom_id = component['custom_id']
                        break
                except KeyError:
                    self.play_id = None
                    custom_id = None
                except Exception as e:
                    debugger.debug(e, 'Messages parsing')
            if custom_id:
                #Set new ids
                self.id = event['id']
                self.play_id = custom_id
        else:
            self.id = None
            self.play_id = None
        
        #Set attributes
        if event != []:
            if event['content']:
                self.content = event['content']
            #Embeds
            if len(event['embeds']) > 0:
                for embed in event['embeds']:
                    try: #Set title
                        self.title = embed['title']
                        try: #Set description
                            self.description = embed['description']
                        except KeyError:
                            pass
                        if self.title == 'You caught:':
                            break
                    except KeyError:
                        self.d = self.sanatize(embed['description'])
                    except Exception as e:
                        self.d = f'[E] Composer error -> {e}'
                        debugger.debug(e, 'Exception - Composer')
                        return None
                return None
            else:
                return None
        else:
            return None

    def build(self, extra: list = []) -> None:
        _tmp = self.description.split('\n')
        for line in _tmp:
            final = ''
            if line.find('LEVEL UP!') > -1:
                #Level up information
                level = sub('[^\d+]', '', sub(r'<.+?> ', '', line))
                final = f'<< LEVEL UP: {int(level) - 1} -> {level} >>'
            elif line.find('<:') > -1:
                #Emotes 
                final = sub(r'  ', ' ', sub(r'<.+?>', '', line))
            elif line.find(':') > -1:
                #Duplicator Emote (and commom emotes)
                final = sub(r'  ', ' ', sub(r':.+?: ', '', line))
            elif line.find('#') > -1: 
                #Global boost information
                pass
            elif line == '' or line == None or line == '\n':
                pass
            else:
                final = line
            self.items.append(sub('[\*+]', '', final))
        if extra != []:
            self.items = extra + self.items
        return None
    
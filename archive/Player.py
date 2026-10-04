
class Player(object):
#Player
#
#This class keeps all the info of what the player is doing, and the moves made.
#So, Player.goRed will update the players location one space in the red direction.
#Player.Location will return the players location.
#
#Later on will add specializations in here, to be loaded from file.
#(Also things like character names etc, which are only useful in expansion)
#


   

    def __init__(self, PlayerName, Colour):
        self.PlayerName = PlayerName
        self.Colour = Colour
        self.Location = "white"
        self.Deck = "top"
        self.Turn = dict()    
        for x in range(0,13):
            self.Turn[str(x+1)] = 'blank'
        
        
    def errhandler(self):
        print("Your input has not been recognised")    
        
        
    #Move Rules
    #---------------------------------------------------------------
    def moveblue(self):
        NewLocation = {
            "blue": "blue",
            "white": "blue",
            "red": "white"}

        print("moving blue")
        self.Location = str(NewLocation.get(self.Location))

    def movered(self):
        NewLocation = {
            "blue": "white",
            "white": "red",
            "red": "red"}
    
        print("moving red")
        self.Location = str(NewLocation.get(self.Location))

    def takelift(self):
        
        NewDeck = {'top': 'bottom', 'bottom': 'top'}
        self.Deck = str(NewDeck.get(self.Deck))

            
    
#-------------------------------------------------------------



    #def addturn(self,turnnumber,action):
    #    Turn.append(turnnumber, action)
    
    
    #def delay(self,turnnumber):
        #move all planned actions up by one 

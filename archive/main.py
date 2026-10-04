
#imports
import Tkinter as tk
import Player


class Starbase(tk.Tk):
    def __init__(self,parent):
        tk.Tk.__init__(self,parent)
        self.parent = parent
        self.initialize()

    def initialize(self):
        container = tk.Frame(self)
        container.pack(side="top", fill="both", expand=True)
        
        #set up window properties and initial focus
        self.geometry('600x250')
        self.resizable(True,True)
        
        container.grid_columnconfigure(0,weight=1)    
        container.grid_rowconfigure(0, weight=1)        
        
        self.frames={}
        for F in (scrMenu, scrBarracks, scrSimulator):
            frame = F(container, self)
            self.frames[F] = frame
            
            frame.grid(row=0, column=0, sticky="nsew")
        
        self.show_frame(scrMenu)
        
    def show_frame(self, cont):
    
        frame = self.frames[cont]
        frame.tkraise()

#Definition of gui Screens
class scrMenu(tk.Frame):

    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent)
                
        #set up window properties and initial focus
        
        self.grid()
        self.grid_columnconfigure(0,weight=1)
        self.grid_columnconfigure(1,weight=3) #button
        self.grid_columnconfigure(2,weight=1)
        self.grid_columnconfigure(3,weight=3) #button
        self.grid_columnconfigure(4,weight=1)
        self.grid_columnconfigure(5,weight=3) #button
        self.grid_columnconfigure(6,weight=1)
    
        
        self.grid_rowconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=2) #title
        self.grid_rowconfigure(2, weight=1)
        self.grid_rowconfigure(3, weight=2) #button
        self.grid_rowconfigure(4, weight=1)
        self.grid_rowconfigure(5, weight=2) #button
        self.grid_rowconfigure(6, weight=1)
        
            
        
        #Title
        
        Title = tk.Label(self, text="Space Alert : Starbase", bg="black", fg="green",bd=2, font="courier", relief="groove")
        Title.grid(column = 1 , row = 1,columnspan =5, sticky = 'nsew')
        
        #text box properties
        #set up text box variable and initialise it
        #self.entryVariable = tk.StringVar()
        #self.entryVariable.set(u"Enter text here.")
        
        #button properties
        button1 = tk.Button(self,text=u"Barracks", width = 1, command=lambda: controller.show_frame(scrBarracks))
        button1.grid(column = 1,row=3, sticky = 'nsew')

        button2 = tk.Button(self,text=u"Training", width = 1, command=lambda: controller.show_frame(scrBarracks))
        button2.grid(column = 3,row=3, sticky = 'nsew')

        button2 = tk.Button(self,text=u"Simulator", width = 1, command=lambda: controller.show_frame(scrSimulator))
        button2.grid(column = 5,row=3, sticky = 'nsew')

        button1 = tk.Button(self,text=u"Library", width = 1, command=lambda: controller.show_frame(scrBarracks))
        button1.grid(column = 1,row=5, sticky = 'nsew')

        button2 = tk.Button(self,text=u"Launch Bay", width = 1, command=lambda: controller.show_frame(scrBarracks))
        button2.grid(column = 3,row=5, sticky = 'nsew')

        button2 = tk.Button(self,text=u"Administration", width = 1, command=lambda: controller.show_frame(scrBarracks))
        button2.grid(column = 5,row=5, sticky = 'nsew')
        
       




class scrBarracks(tk.Frame):

    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent)
        
                #set up window properties and initial focus
        
        self.grid()
        self.grid_columnconfigure(0,weight=1)
        self.grid_columnconfigure(1,weight=3) #button
        self.grid_columnconfigure(2,weight=1)
        self.grid_columnconfigure(3,weight=3) #button
        self.grid_columnconfigure(4,weight=1)
        self.grid_columnconfigure(5,weight=3) #button
        self.grid_columnconfigure(6,weight=1)
    
        
        self.grid_rowconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=2) #title
        self.grid_rowconfigure(2, weight=1)
        self.grid_rowconfigure(3, weight=2) #button
        self.grid_rowconfigure(4, weight=1)
        self.grid_rowconfigure(5, weight=2) #button
        self.grid_rowconfigure(6, weight=1)
         
        
        #Title
        
        Title = tk.Label(self, text="Barracks", bg="black", fg="green",bd=2, font="courier", relief="groove")
        Title.grid(column = 1 , row = 1,columnspan =5, sticky = 'nsew')
               
       
        btnReturn = tk.Button(self, text="Done", command=lambda: controller.show_frame(scrMenu))
        btnReturn.grid(column = 5, row=5, sticky = "nsew")


        
        
        
class scrSimulator(tk.Frame):

    #Setup Dimensions
        
    #Ship Position
    BridgeCentre = 450
    BridgeFront = 50
        
    #Cabin Size
    CabinHeight = 200
    CabinWidth = 200
        
    #Layout
    DeckOffset = 20
 
    #GravLifts
    GravLiftWidth = 40
    GravliftHeight = 20



    def background(self, w):
                      

        #White Deck
        TDW_1x = self.BridgeCentre - (self.CabinWidth / 2)
        TDW_1y = self.BridgeFront
        TDW_2x = self.BridgeCentre + (self.CabinWidth / 2)
        TDW_2y = self.BridgeFront + self.CabinHeight
        
        GLO_y = self.GravliftHeight/2
        GLO_x = self.GravLiftWidth / 2
              
        w.create_rectangle(TDW_1x, TDW_1y, TDW_2x , TDW_2y , fill="white") # Bridge
        w.create_rectangle(TDW_1x, TDW_1y + self.CabinHeight, TDW_2x , TDW_2y + self.CabinHeight , fill="white") # Engineering
        w.create_oval(self.BridgeCentre - GLO_x, TDW_2y + GLO_y, self.BridgeCentre + GLO_x, TDW_2y - GLO_y,fill="yellow", width = 3) # gravlift
        
        #RedDeck
        
        TDR_1x = TDW_1x - self.CabinWidth
        TDR_1y = TDW_1y + self.DeckOffset
        TDR_2x = TDW_2x - self.CabinWidth
        TDR_2y = TDW_2y + self.DeckOffset
        
        w.create_rectangle(TDR_1x, TDR_1y, TDR_2x , TDR_2y , fill="red") # Bridge
        w.create_rectangle(TDR_1x, TDR_1y + self.CabinHeight, TDR_2x , TDR_2y + self.CabinHeight , fill="red") # Engineering
        
        w.create_oval(
            self.BridgeCentre - self.CabinWidth - GLO_x, 
            TDR_2y + GLO_y, 
            self.BridgeCentre - self.CabinWidth + GLO_x, 
            TDR_2y - GLO_y, 
            fill="yellow", width = 3) # gravlift
        
        #BlueDeck
        
        TDB_1x = TDW_1x + self.CabinWidth
        TDB_1y = TDW_1y + self.DeckOffset
        TDB_2x = TDW_2x + self.CabinWidth
        TDB_2y = TDW_2y + self.DeckOffset
        
        w.create_rectangle(TDB_1x, TDB_1y, TDB_2x , TDB_2y , fill="blue") # Bridge
        w.create_rectangle(TDB_1x, TDB_1y + self.CabinHeight, TDB_2x , TDB_2y + self.CabinHeight , fill="blue") # Engineering
        w.create_oval(self.BridgeCentre + self.CabinWidth - GLO_x, TDR_2y + GLO_y, self.BridgeCentre + self.CabinWidth + GLO_x, TDR_2y - GLO_y , fill="yellow", width = 3) # gravlift


    def get_loc_coords(self,w,Cabin,Position):
        
        #setup currently to just place red, more later
             
        #define positions
        player_radius = 10 
        
        #top white
        #Cabin Centres
        if Cabin == "TW":
           CabCentre = [self.BridgeCentre, (self.BridgeFront + self.CabinHeight / 2)]
        elif Cabin == "TR":
           CabCentre = [self.BridgeCentre - self.CabinWidth, (self.BridgeFront + self.CabinHeight / 2) + self.DeckOffset]
        elif Cabin == "TB":
           CabCentre = [self.BridgeCentre + self.CabinWidth, (self.BridgeFront + self.CabinHeight / 2) + self.DeckOffset]
           
        elif Cabin == "BW":
           CabCentre = [self.BridgeCentre, (self.BridgeFront + self.CabinHeight / 2) + self.CabinHeight]
        elif Cabin == "BR":
           CabCentre = [self.BridgeCentre - self.CabinWidth, (self.BridgeFront + self.CabinHeight / 2)  + self.DeckOffset + self.CabinHeight]   
        elif Cabin == "BB":
           CabCentre = [self.BridgeCentre + self.CabinWidth, (self.BridgeFront + self.CabinHeight / 2)  + self.DeckOffset + self.CabinHeight]   

             
        #position offsets
        if Position == 1:      
            PosOffset = [0, -self.CabinHeight * 0.20]
        elif Position == 2:      
            PosOffset = [self.CabinWidth * 0.25, 0]
        elif Position == 3:      
            PosOffset = [-self.CabinWidth * 0.25, 0]
        elif Position == 4:      
            PosOffset = [self.CabinWidth * 0.15, self.CabinHeight * 0.25]
        elif Position == 5:      
            PosOffset = [-self.CabinWidth * 0.15, self.CabinHeight * 0.25]
                
        pos1 = [CabCentre[0] + PosOffset[0],CabCentre[1] + PosOffset[1]] #Cabin + offset
        Pos = [(pos1[0] - player_radius),(pos1[1] - player_radius),(pos1[0] + player_radius),(pos1[1] + player_radius)] #cabin + offset + player radius
        return Pos
        
    def Player_Move(self, w, PlayerTag,Cab,Spot):
        
        #inputs
            #required location
            target = self.get_loc_coords(w,Cab,Spot)
            current = w.coords(PlayerTag)
            
            currentx = current[0]
            currenty = current[1]
            
            targetx = target[0]            
            targety = target[1]
            
            print("X",currentx,targetx)
            print("Y",currenty,targety)
           
            #Determine move direction (if x < then +1 if x > then -1) same with y
            if (currentx > targetx):
                movex = -1
            elif (targetx > currentx):
                movex = 1
            elif (targetx == currentx):
                movex = 0
             
            #Determine move direction (if x < then +1 if x > then -1) same with y
            if (currenty > targety):
                movey = -1
            elif (targety > currenty):
                movey = 1
            elif (targety == currenty):
                movey = 0
                
            #move towards required coordinates 
            w.move(PlayerTag, movex, movey)
            
            #Check if coords = required location
            if not(movex == 0 and movey == 0):
                self.after(50, self.Player_Move(w,PlayerTag,Cab,Spot ))
            else:
                print("done")
        
            

        
        
        
        
        
    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent)
        
                #set up window properties and initial focus
        
        self.grid()
        
        for c in range(0,20):
            self.grid_columnconfigure(c,weight=1)
        
        for r in range(0,20):
            self.grid_rowconfigure(r, weight=1)
 
        
        #Title
        
        Title = tk.Label(self, text="Simulator", bg="black", fg="green",bd=2, font="courier", relief="groove")
        Title.grid(column = 1 , row = 1,columnspan =(c-1), sticky = 'nsew')
          
        #canvas element        
        w = tk.Canvas(self, width=900, height=500,
           borderwidth=0,
           highlightthickness=0,
           background='black')
        w.grid(column = 2, row = 1, columnspan=c-1, rowspan = r-1)   
         
        #close button
        btnReturn = tk.Button(self, text="Done", command=lambda: controller.show_frame(scrMenu))
        btnReturn.grid(column = c-1, row=r-1, sticky = "nsew")
        
                
        #draw ship
        self.background(w)
        
        #drop in players
        Pos = self.get_loc_coords(w,"TW",1)
        Player1 = w.create_oval(Pos[0],Pos[1],Pos[2],Pos[3], fill="red", width=2)
        
        Pos = self.get_loc_coords(w,"BW",1)
        Player2 = w.create_oval(Pos[0],Pos[1],Pos[2],Pos[3], fill="blue", width=2)
        
        Pos = self.get_loc_coords(w,"TR",1)
        Player3 = w.create_oval(Pos[0],Pos[1],Pos[2],Pos[3], fill="green", width=2)
        
        Pos = self.get_loc_coords(w,"TB",1)
        Player4 = w.create_oval(Pos[0],Pos[1],Pos[2],Pos[3], fill="yellow", width=2)
        
        Pos = self.get_loc_coords(w,"BB",1)
        Player5 = w.create_oval(Pos[0],Pos[1],Pos[2],Pos[3], fill="purple", width=2)
        
        
        #Test Move Button
        btnMove = tk.Button(self, text="TestMove", command= lambda: self.Player_Move(w,w.find_withtag(Player5),"TW",2 ))
        btnMove.grid(column = 10, row=r-1, sticky = "nsew")     

       
    
     
   
        
        
        

        
        
                
        
if __name__ == "__main__":
    app = Starbase(None)
    app.title('Space Alert: Starbase')
    app.mainloop()


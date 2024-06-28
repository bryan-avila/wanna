import ttkbootstrap as ttk
import pymongo
from typing import List

# Establish connection to local MongoDB
my_client = pymongo.MongoClient("mongodb://localhost:27017/")
my_db = my_client['Wanna']

# WINDOW FRAME (will either have main or entry as the currently displayed 'view')
class Wanna(ttk.Window):
    def __init__(self):
        # Window Adjusting
        super().__init__()
        self.title('Wanna App')
        self.force_app_middle_launch(1200, 700)
        self.minsize(1200,700)
        self.bind('<Escape>', lambda event: self.quit())

        # Styling
        ttk.Style().theme_use('superhero')
        ttk.Style().configure("Treeview.Heading", foreground="gold")
        ttk.Style().configure("Treeview", font=('Helvetica', 10))

        # Add frames to this window
        self.top_frame = TopFrame(self)
        self.add_more_frame = AddMoreFrame(self)
        self.entry_frame = EntryFrame(self)
        self.main_frame = MainFrame(self)
        self.bottom_frame = BottomFrame(self)

        self.remove_empty_collections()
        self.validate_mongoDB()
        self.mainloop() # Run it!

    # Remove empty collections, if they exist, before anything else!
    def remove_empty_collections(self):
        current_collection = 0
        while current_collection < len(my_db.list_collection_names()):
            my_collection = my_db[my_db.list_collection_names()[current_collection]] # Connect to the collection in curr_collec position
            if(my_collection.estimated_document_count() == 0):
                print("Deleting Collection", my_collection)
                current_collection = current_collection + 1
                my_collection.drop()
            current_collection = current_collection + 1
    
    # Function that checks if collections/docs exist in local mongoDB. Populates with ServiceFrames if there is data. Ignore collections that have none.
    def validate_mongoDB(self):
        if len(my_db.list_collection_names()) > 0:
            print("MongoDB Collections Found. Populating window with ServiceFrame(s)")
            current_collection = 0
            while current_collection < len(my_db.list_collection_names()):
                entries: List[str] = [] # List that holds mongoDB string data: service, title, season, ep.
                additional_item = 4 # Variable that holds the position after a service tree has been created (service, title, season, ep.)

                entries.append(my_db.list_collection_names()[current_collection]) # Append service title

                my_collection = my_db[my_db.list_collection_names()[current_collection]]

                # Check if current collection has no documents. Skip over this iteration!
                if(my_collection.estimated_document_count() == 0):
                    print("NO DOCUMENTS FOUND FOR SERVICE: ", entries[0])
                    current_collection = current_collection + 1
                    my_collection.drop()
                    continue

                for document in my_collection.find({}, {"_id": 0}):
                    for key, value in document.items():
                        entries.append(value) # Append title (only once per service tree), then title, season, ep

                self.mongo_frame = ServiceFrame(self.main_frame) # Create service frame per collection
                self.mongo_frame.create_label(entries[0])
                self.mongo_frame.create_treeview()
                self.mongo_frame.insert_into_treeview(entries[1], entries[2], entries[3])
                self.mongo_frame.create_add_more_episodes_button()
                self.entry_frame.place_forget()

                if(len(entries) > 4): # Does the current TreeView have more than 1 item? (service, title, season, ep make up one item)
                    while(additional_item < len(entries)):
                        self.mongo_frame.insert_into_treeview(entries[additional_item], entries[additional_item + 1], entries[additional_item + 2])
                        additional_item = additional_item + 3
                current_collection = current_collection + 1
        else:
            print("No MongoDB Collections found. Click the 'Add Service' button to start your watch list!")

    # Function called from within bottom_frame. Passed argument changes which frame at top of the place stack/if a treeview has been added more items
    def change_window_frame(self, reveal_order):
        if reveal_order == "reveal_entry": # Remove all of main frame, present entry frame.
            self.main_frame.place_forget() 
            self.entry_frame.clear_entry_text() 
            self.entry_frame.place(relx=0, rely=0.15, relwidth=1, relheight=0.70)

        elif reveal_order == "reveal_main": # Using info from Entry Frame, place data into MongoDB and into new treeview.
            user_entries: List[str] = self.entry_frame.return_entries() 

            if(not user_entries[0] or not user_entries[1] or not user_entries[2] or not user_entries[3]):
                print("Error. Missing Entry Frame information.")
                self.entry_frame.place_forget() 
                self.main_frame.place(relx=0, rely=0.15, relwidth=1, relheight=0.70) 
            else: 
                my_collection = my_db[user_entries[0]]
                my_collection.insert_one({"title": user_entries[1], "season": user_entries[2], "episode": user_entries[3]})

                self.entry_frame.place_forget() 
                self.main_frame.place(relx=0, rely=0.15, relwidth=1, relheight=0.70) 

                self.create_service_treeview(user_entries) # Display a new TreeView, passing info from entry_frame

        elif reveal_order == "add_to_treeview": # Using info from Add More Frame, place data into MongoDB and into existing treeview.
            user_entries: List[str] = self.add_more_frame.return_entries()

            if (not user_entries[0] or not user_entries[1] or not user_entries[2]): # Nothing added to entry? Error!
                print("Error. Missing Add More Frame information") 
                self.add_more_frame.clear_entry_text()
                self.add_more_frame.place_forget()
                self.bottom_frame.prepare_bottom_for_adding_service()
                self.main_frame.place(relx=0, rely=0.15, relwidth=1, relheight=0.70)

            else:
                my_collection = my_db[self.tree_view_label]
                my_collection.insert_one({"title": user_entries[0], "season": user_entries[1], "episode": user_entries[2]})

                self.tree_view.insert_into_treeview(user_entries[0], user_entries[1], user_entries[2]) # Add to tree view!

                self.add_more_frame.clear_entry_text()
                self.add_more_frame.place_forget()
                self.bottom_frame.prepare_bottom_for_adding_service()
                self.main_frame.place(relx=0, rely=0.15, relwidth=1, relheight=0.70)

    # Function called from within change_window_frame function.
    def create_service_treeview(self, entries):
        self.service_frame = ServiceFrame(self.main_frame)
        self.service_frame.create_label(entries[0])
        self.service_frame.create_treeview()
        self.service_frame.insert_into_treeview(entries[1], entries[2], entries[3]) 
        self.service_frame.create_add_more_episodes_button()
        self.entry_frame.place_forget() 

    # Called from Main Frame, which itself is called from ServiceFrame.
    def add_to_treeview(self, tree_view, service_label):
        # Hide main_frame, prepare bottom_frame, place the add_more frame to be visible, 
        # and grab the reference to this instance of treeview as well as the label of the tree view
        self.main_frame.place_forget()
        self.bottom_frame.prepare_bottom_for_adding_episodes() # Disable add service button while users add more to a treeview. 
        self.add_more_frame.change_service_label(service_label)
        self.add_more_frame.place(relx=0, rely=0.15, relwidth=1, relheight=0.70)
        self.tree_view = tree_view # Create an instance of the passed treeview
        self.tree_view_label = self.tree_view.return_label() # Create an instance of the passed treeview label

    # Force the window to launch in the middle of your display's resolution
    def force_app_middle_launch(self, width, height):
        window_width = width
        window_height = height
        display_width = self.winfo_screenwidth()
        display_height = self.winfo_screenheight()
        left_position = int(display_width / 2 - window_width / 2)
        top_position = int(display_height / 2 - window_height / 2)

        self.geometry(f'{window_width}x{window_height}+{left_position}+{top_position}')

# TOP FRAME (app title)
class TopFrame(ttk.Frame):
    def __init__(self, master):
        super().__init__(master)
        
        # Place this frame
        self.place(relx=0, rely=0, relwidth=1, relheight=0.15)

        # Create Label widget
        self.label_title = ttk.Label(master=self, text='Wanna', font=('Verdana', 28, 'bold'), foreground='#F8C109', anchor='center')

        # Add widget to layout
        self.label_title.pack(pady=20)

# BOTTOM FRAME (add service/treeview and confirm entries buttons)
class BottomFrame(ttk.Frame):
    def __init__(self, master):
        super().__init__(master)

        # Wanna window is the master
        self.master_window = master

        # Place this frame
        self.place(relx=0, rely=1, relwidth=1, relheight=0.15, anchor='sw')

        # Create Label widget
        self.add_service_button = ttk.Button(master=self, text='Add Streaming Service', command=self.reveal_entry_frame)
        self.confirm_entries_button = ttk.Button(master=self, text='Confirms Entries', command=self.reveal_main_frame)

        # Add widgets to layout
        self.add_service_button.place(relx=1, rely=1, anchor='se')
        self.confirm_entries_button.place(relx=0, rely=1, anchor='sw')
        self.confirm_entries_button.configure(state='disabled') # Confirm Entries button initially disabled.

    # "Add Service" Button causes EntryFrame to be placed over MainFrame using Wanna's function.
    def reveal_entry_frame(self):
        self.add_service_button.configure(state='disabled')
        self.confirm_entries_button.configure(state='enabled') 
        self.master_window.change_window_frame("reveal_entry") 

    # "Confirm Entries" Button causes MainFrame to be placed over EntryFrame using Wanna's function.
    def reveal_main_frame(self):
        self.add_service_button.configure(state='enabled')
        self.confirm_entries_button.configure(state='disabled')
        self.master_window.change_window_frame("reveal_main")

    # "Confirm Entries" reveal the newly added content in Main Frame treeview using Wanna's function.
    def reveal_treeview_additions(self):
        self.master_window.change_window_frame("add_to_treeview")
    
    # Called by Wanna to disable add more service button when adding new episodes to a tree view.
    def prepare_bottom_for_adding_episodes(self):
        self.add_service_button.configure(state='disabled')
        self.confirm_entries_button.configure(command=self.reveal_treeview_additions) # Change function.
        self.confirm_entries_button.configure(state='enabled')

    # Called by Wanna after new episodes have been add to a tree. Allow users to add new entries.
    def prepare_bottom_for_adding_service(self):
        self.add_service_button.configure(state='enabled')
        self.confirm_entries_button.configure(state='disabled')
        self.confirm_entries_button.configure(command=self.reveal_main_frame) # Revert function to original.

# MAIN FRAME (can house service frames)
class MainFrame(ttk.Frame):
    def __init__(self, master):
        self.master = master
        super().__init__(master)
        self.place(relx=0, rely=0.15, relwidth=1, relheight=0.70)
    
    # Called by ServiceFrame when Add More button is clicked! Passed this tree view to Wanna
    def change_into_add_more_frame(self, tree_view, service_label):
        self.master.add_to_treeview(tree_view, service_label)

# ENTRY FRAME (leads to creation of service frames. holds four entry fields)
class EntryFrame(ttk.Frame):
    def __init__(self, master):
        super().__init__(master)

        # Place this frame
        self.place(relx=0, rely=0.15, relwidth=1, relheight=0.70)

        self.user_serv_name = ttk.StringVar() # Create variables for the entry text
        self.user_show_name = ttk.StringVar()
        self.user_seas_num = ttk.StringVar()
        self.user_ep_num = ttk.StringVar()

        self.create_entry_frame_widgets()
        self.create_entry_frame_layout()

    def create_entry_frame_widgets(self):
        # Create Entries and bind them with 'Up Arrow Key' & 'Down Arrow Key' to move between the entries
        self.service_name = ttk.Entry(master=self, textvariable=self.user_serv_name, style='info.TEntry')
        self.service_name.bind('<Up>', lambda event: self.show_name.focus())

        self.show_name = ttk.Entry(master=self, textvariable=self.user_show_name, style='info.TEntry')
        self.show_name.bind('<Up>', lambda event: self.season_number.focus())
        self.show_name.bind('<Down>', lambda event: self.service_name.focus())

        self.season_number = ttk.Entry(master=self, textvariable=self.user_seas_num, style='info.TEntry', width=5)
        self.season_number.bind('<Up>', lambda event: self.episode_number.focus())
        self.season_number.bind('<Down>', lambda event: self.show_name.focus())

        self.episode_number = ttk.Entry(master=self, textvariable=self.user_ep_num, style='info.TEntry', width=5)
        self.episode_number.bind('<Down>', lambda event: self.season_number.focus())

        self.label_service_name = ttk.Label(master=self, text="Streaming Service", font=('Serif', 12), foreground='gold')
        self.label_show_name = ttk.Label(master=self, text="Show Name", font=('Serif', 12), foreground='gold')
        self.label_season_number = ttk.Label(master=self, text="Season #", font=('Serif', 12), foreground='gold')
        self.label_episode_number = ttk.Label(master=self, text="Episode #", font=('Serif', 12), foreground='gold')

    def create_entry_frame_layout(self):
        self.columnconfigure((0,1,2,3), weight=1)
        self.rowconfigure(0, weight=1)
        self.rowconfigure(1, weight=4)

        self.service_name.grid(row=1, column=0)
        self.label_service_name.grid(row=0, column=0, rowspan=2)

        self.show_name.grid(row=1, column=1)
        self.label_show_name.grid(row=0, column=1, rowspan=2)

        self.season_number.grid(row=1, column=2)
        self.label_season_number.grid(row=0, column=2, rowspan=2)

        self.episode_number.grid(row=1, column=3)
        self.label_episode_number.grid(row=0, column=3, rowspan=2)

    def return_entries(self):
        entries: List[str] = [self.user_serv_name.get(), self.user_show_name.get(), self.user_seas_num.get(), self.user_ep_num.get()] 
        return entries # Return a list of all entry fields
    
    def clear_entry_text(self):
        self.service_name.delete(0, 'end')
        self.show_name.delete(0, 'end')
        self.episode_number.delete(0, 'end')
        self.season_number.delete(0, 'end')

# ADD MORE FRAME (add more to an existing treeview. holds three entry fields)
class AddMoreFrame(ttk.Frame):
    def __init__(self, master):
        super().__init__(master)
        self.place(relx=0, rely=0.15, relwidth=1, relheight=0.70)

        self.user_defined_service = ttk.StringVar() # Will be set by whatever the treeview's service name is.
        self.user_show_name = ttk.StringVar()
        self.user_seas_num = ttk.StringVar()
        self.user_ep_num = ttk.StringVar()

        self.create_add_more_frame_widgets()
        self.create_add_more_frame_layout()

    # Similar to EntryFrame. Only 3 entry fields. 
    def create_add_more_frame_widgets(self):
        # Create Entries and bind them with 'Up Arrow Key' and 'Down Arrow Key'
        self.show_name = ttk.Entry(master=self, textvariable=self.user_show_name, style='info.TEntry')
        self.show_name.bind('<Up>', lambda event: self.season_number.focus())

        self.season_number = ttk.Entry(master=self, textvariable=self.user_seas_num, style='info.TEntry', width=5)
        self.season_number.bind('<Up>', lambda event: self.episode_number.focus())
        self.season_number.bind('<Down>', lambda event: self.show_name.focus())

        self.episode_number = ttk.Entry(master=self, textvariable=self.user_ep_num, style='info.TEntry', width=5)
        self.episode_number.bind('<Down>', lambda event: self.season_number.focus())

        self.label_user_defined_service = ttk.Label(master=self, textvariable=self.user_defined_service, font=('Serif', 22), foreground='#FCCE37', anchor='center', relief=ttk.RAISED)
        self.label_show_name = ttk.Label(master=self, text="Show Name", font=('Serif', 12), foreground='gold')
        self.label_season_number = ttk.Label(master=self, text="Season #", font=('Serif', 12), foreground='gold')
        self.label_episode_number = ttk.Label(master=self, text="Episode #", font=('Serif', 12), foreground='gold')

    # Similar to EntryFrame. Only 3 columns in the grid. 
    def create_add_more_frame_layout(self):
        self.user_defined_service.set("DEFAULT")

        self.columnconfigure((0,1,2), weight=1)
        self.rowconfigure(0, weight=1)
        self.rowconfigure(1, weight=4)

        self.label_user_defined_service.grid(row=0, column=0, sticky='s', columnspan=3, ipady=10, ipadx=15)

        self.show_name.grid(row=1, column=0)
        self.label_show_name.grid(row=0, column=0, rowspan=2)

        self.season_number.grid(row=1, column=1)
        self.label_season_number.grid(row=0, column=1, rowspan=2)

        self.episode_number.grid(row=1, column=2)
        self.label_episode_number.grid(row=0, column=2, rowspan=2)

    def return_entries(self):
        entries: List[str] = [self.user_show_name.get(), self.user_seas_num.get(), self.user_ep_num.get()] 
        return entries # Return a list of all entry fields
    
    def clear_entry_text(self):
        self.show_name.delete(0, 'end')
        self.episode_number.delete(0, 'end')
        self.season_number.delete(0, 'end')

    def change_service_label(self, text):
        self.user_defined_service.set(text)

# SERVICE FRAME (holds a treeview and a button)
class ServiceFrame(ttk.Frame):
    def __init__(self, master):
        super().__init__(master)
        self.master = master # Connect this frame with Main Frame
        self.pack(side='left', expand=True, fill='both', pady=10, padx=10) # Pack this inside Main Frame!

    # Create a label with the show's title as the text. Called from within Wanna().
    def create_label(self, label_text):
        service_label = ttk.Label(master=self, text=label_text, font=('Helvtica', 20), foreground='#FCCE37')
        self.service_name = label_text # Keep track of this treeview's service name
        service_label.pack(pady=25, expand=True, anchor='center')

    # Return label that will be used to identify mongoDB collection
    def return_label(self):
        return self.service_name

    # Create a treview. Called from within Wanna.
    def create_treeview(self):
        self.tree_view = ttk.Treeview(master=self, columns=('show_title', 'show_season', 'show_episode'), show='headings')
        self.tree_view.heading('show_title', text='Title')
        self.tree_view.heading('show_season', text='Season')
        self.tree_view.heading('show_episode', text='Episode')

        self.tree_view.column('show_title', stretch=True, anchor='center')
        self.tree_view.column('show_season', width=150, stretch=False, anchor='center')
        self.tree_view.column('show_episode', width=150, stretch=False, anchor='center')

        self.tree_view.bind('<Delete>', self.remove_from_tree)
        self.tree_view.bind('<<TreeviewSelect>>', self.highlight_selected_item)
        self.tree_view.bind('<f>', lambda event: self.add_to_this_tree()) # Bind letter 'f' to add without using mouse

        self.tree_view.pack(pady=15, expand=True, fill='both')
    
    # Create a button that allows users to add more episodes to the specified treeview
    def create_add_more_episodes_button(self):
        add_to_treeview_button = ttk.Button(master=self, text='Add to Watch List', command=self.add_to_this_tree)
        add_to_treeview_button.pack(expand=True, fill='both', padx=100)

    # Using ttk variables handled by Wanna, insert values entered from entry_frame
    def insert_into_treeview(self, title, season, episode):
        self.tree_view.insert(parent='', index=ttk.END, values=(title, season, episode))

    # Function for when 'add more episodes' button is pressed. Pass this instance of treeview to main frame (the master).
    def add_to_this_tree(self):
        self.master.change_into_add_more_frame(self, self.service_name)

    # Allow items to be highlighted
    def highlight_selected_item(self, _):
        for i in self.tree_view.selection():
            self.tree_view.focus(item=i)

    # Allow items to be deleted. Update MongoDB accordingly!
    def remove_from_tree(self, _):
        if self.service_name in my_db.list_collection_names():
            print(f"{self.service_name} does exist in MongoDB. Preparing deletion of item..")

        my_collection = my_db[self.service_name]

        for i in self.tree_view.selection():
            print("Deleted item(s) ", self.tree_view.item(i)['values'])
            my_collection.delete_one({"title": str(self.tree_view.item(i)['values'][0]), "season": str(self.tree_view.item(i)['values'][1]), "episode": str(self.tree_view.item(i)['values'][2])})
            self.tree_view.delete(i)

            # If the tree view has no items/children, then remove it in real time
            if(not self.tree_view.get_children()):
                print("Empty Tree View found, deleting it.....")
                self.destroy()
            
# Run the App!
Wanna()

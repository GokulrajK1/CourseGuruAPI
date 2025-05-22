class Name: 
    def __init__(self, first="", middle="", last=""):
        self.first = first
        self.middle = middle
        self.last = last 

    def get_components(self) -> tuple:
        return self.first, self.middle, self.last
    
    @classmethod
    def from_scraped_name(cls, scraped_name):
        if scraped_name == "Unknown" or scraped_name == None:
            return cls()
        
        names = [name.strip() for name in scraped_name.split(",")]
        first, middle, last = "", "", ""

        # Speical Check for Error in Rutgers Data
        if len(names) > 2 and "DU" in names:
            print("HELLO???")
            names.remove("DU")
            names.remove("JISHEN")
            names = names[0].split(" ")
            print(names)
        # End of Special Check May Be Removed Later

        if len(names) == 1 and "-" not in names[0]:
            last = names[0].capitalize()

        elif len(names) == 1 and "-" in names[0]:
            middle, last = names[0].split('-')[0].capitalize(), names[0].split('-')[1].capitalize()

        elif len(names) == 2 and " " not in names[1]:
            first, last = names[1].capitalize(), names[0].capitalize()

        elif len(names) == 2 and " " in names[1]:
            first, middle, last = names[1].split(" ")[0].capitalize(), names[1].split(" ")[1].capitalize(), names[0].capitalize()

        elif len(names) > 2:
            first, middle, last = names[2].capitalize(), names[0].capitalize(), names[1].capitalize()

        return cls(first, middle, last)
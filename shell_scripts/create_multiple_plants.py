

# django shell:
# exec(open('shell_scripts/create_multiple_plants.py').read())

from plants.models      import  Log
from users.models       import  User
from plants.services    import  create_log, \
                                create_new_plant

# Set user owner ID for new plants
USER_ID = 1

# Set path to csv file
CSV_FILE = 'shell_scripts/mesembs_utf.csv'


class PlantCreator:

    def __init__(self, user_id: int, csv_file_name: str):
        self.user = User.objects.get(id=user_id)
        self.csv_file_name = csv_file_name
        self.data = None
        self.attr_names = []

        self.read_data_from_file()
        self.read_header()

    def read_data_from_file(self):
        with open(self.csv_file_name, 'r') as f:
            self.data = f.readlines()

    def read_header(self):
        for attr in self.data[0].replace('\n', '').split(';'):
            #if attr:
            self.attr_names.append(attr)
        self.data.pop(0)

    def create_objects(self):
        for line in self.data:
            # create plant
            new_plant = create_new_plant(self.user)

            # prepare data dict
            data_dic = self.str_to_dic(line)
            data_dic['owner'] = self.user.id

            # create log
            create_log(
                Log.ActionChoices.ADDITION,
                self.user,
                new_plant,
                data_dic
            )

            print(f'Plant #{new_plant.uid} was created')

    def str_to_dic(self, line: str):
        dic = {}
        line = line.replace('\n', '').split(';')
        for i in range(len(line)):
            if self.attr_names[i] and line[i]:
                dic[self.attr_names[i]] = line[i]
        return dic
    

    def show_data(self):
        print(self.attr_names)



app = PlantCreator(USER_ID, CSV_FILE)
app.create_objects()

print('ok')

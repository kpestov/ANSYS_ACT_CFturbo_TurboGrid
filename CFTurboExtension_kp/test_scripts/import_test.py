
class MyFile():
    file_name = None

    # def __init__(self, file_name):
    #     self.file_name = file_name

    def write_file(self, file_name):
        with open(file_name, 'w') as f:
            f.write('hui')


file_1 = MyFile()
# file_1.write_file('pestov.txt')





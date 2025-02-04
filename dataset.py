import csv
import os

if __name__ == "__main__":
    
    input_csv_file = "Books_rating4.csv"
    output_directory = "/Users/eliacapiluppi/Desktop/GestInfPratico/Dataset"

    counters_dict = {}
    
    # Crea directory
    if not os.path.exists(output_directory):
        os.makedirs(output_directory)
    
    with open(input_csv_file, 'r', newline='', encoding='utf-8') as csv_file:
        csv_reader = csv.reader(csv_file)
        next(csv_reader, None) #skippa header
        for row in csv_reader:
            key = tuple(row[0:2])
            counter = counters_dict.get(key, 0) + 1
            counters_dict[key] = counter

            output_txt_file = os.path.join(
                output_directory,
                f'{row[0]}_{counter}.txt'
            )
            with open(output_txt_file, 'w', encoding='utf-8') as txt_file:
                for element in row:
                    txt_file.write(element.strip() + '\n')
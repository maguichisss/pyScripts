import os
import csv
import logging
import pandas as pd
from time import time
from glob import glob

logger = logging.getLogger(__name__)

def is_file(file):
    # find a file using wild card like /path/to/file*.xml
    file = glob(file)[0]
    if os.path.isfile(file):
        return file
    else:
        raise argparse.ArgumentTypeError(f"{file} is not a valid file")

def valid_rows_cols(csv1, csv2):
    # raise if the rows doesnt match
    if len(csv1) != len(csv2):
        print("csv1", len(csv1), "csv2", len(csv2))
        raise Exception("DIFFERENT ROWS")
    # raise if the columns doesnt match
    if csv1.columns.all() != csv2.columns.all():
        print(csv1.columns)
        print(csv2.columns)
        raise Exception("DIFFERENT COLUMNS")
    print("csv1:", csv1.shape, "csv2:", csv2.shape)

def main(pathcsv1, pathcsv2):
    csv1 = pd.read_csv(pathcsv1, header=None)
    csv2 = pd.read_csv(pathcsv2, header=None)
    valid_rows_cols(csv1, csv2)
    # get the column name which are different
    # and drop the equal columns
    diff_cols = []
    for i,col in enumerate(csv1.columns):
        if not csv1[col].equals(csv2[col]):
            #print(f"col #{i+1} {col} is different")
            diff_cols.append(col)
        else:
            csv1.drop(col, inplace=True, axis=1)
            csv2.drop(col, inplace=True, axis=1)
    if not diff_cols:
        print("ALL columns are equal")
    print(f"cols {diff_cols} are different")
    # add flags
    csv1['flag'] = 'csv1'
    csv2['flag'] = 'csv2'
    csv1['diffCols'] = ''
    csv2['diffCols'] = ''
    # set a column with the columns that are different
    nrows = len(csv1)
    for i in range(nrows):
        cols_d = []
        for col in diff_cols:
            if pd.isnull(csv1[col][i]) and pd.isnull(csv2[col][i]):
                continue
            elif csv1[col][i] != csv2[col][i]:
                cols_d.append(col)
        if cols_d:
            csv1["diffCols"][i] = ";".join([str(x) for x in cols_d])
            csv2["diffCols"][i] = ";".join([str(x) for x in cols_d])
    aux = pd.concat([csv1, csv2])
    # drop the row that are equal
    aux.drop_duplicates(inplace=True, keep=False, subset=diff_cols)
    aux = aux.sort_index()
    print(aux.shape)
    acc = 100 - (len(aux)/nrows*100)
    print(f"{acc:.5f}% is equal")
    # export result to csv
    if len(aux):
        aux.to_csv("diff_csv.csv", quotechar='"',  quoting=csv.QUOTE_ALL)


if __name__ == "__main__":
    """Compare 2 CSVs
    python -m carma_xml_parser.csv2db path/to/data.csv /path/to/csvold
    python -m carma_xml_parser.csv2db path/to/data.csv /path/to/csvnew
    """
    import sys
    import argparse

    parser = argparse.ArgumentParser(description="Compare 2 CSVs")
    parser.add_argument('csvold', type=is_file, help="CSV old to compare")
    parser.add_argument('csvnew', type=is_file, help="CSV new to compare")
    #parser.add_argument('--inputfile', help="Csv name to insert separated by commas")
    args = parser.parse_args()

    try:
        print("%s - %s" % (args.csvold, args.csvnew))
        start_time = time()    
        main(args.csvold, args.csvnew)
        print("Finished in %.2f seconds." % (time() - start_time))    
        sys.exit(0)
    except Exception as e:
        logger.exception(e)
        sys.exit(1)

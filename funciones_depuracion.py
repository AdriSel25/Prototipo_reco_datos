import math
import os
import csv 
import shutil
from os import path
import re

def procesar(id_admin, diccionario, lista_procesado, lista_depuracion):
    if (id_admin in lista_depuracion):
        # continuacion para que simplemente borre el comercio
        print("Ya se ha procesado este admin...")

    else:
        print("El admin no ha sido procesado, borraremos sus relaciones\n")
        for comercios_diccionario in diccionario[id_admin]:
            # un for para recorrer los comercios del diccionario por admin
            print("Se agrega ID de admin  y comercio para borrar la relacion")
            lista_depuracion.append([comercios_diccionario,id_admin])
            print(comercios_diccionario, id_admin+"\n")
        lista_procesado.append(id_admin)
        print(f"Los admins procesador son: {lista_procesado}\n")

def creacion_csv(lista_depuracion, nombre_archivo, lista_incompletos):
    filas_total = len(lista_depuracion)
    archivos_total = math.ceil(filas_total/15)

    print(f"Cantidad de filas: {filas_total}")
    print(f"Archivos de depuracion por crear: {archivos_total}")
    indice_min = 0

    indice_max = 15

    # Nombre del archivo ZIP de salida
    output_filename = f'archivos_depuracion_{nombre_archivo}'

    for x in range (1, archivos_total + 1):
        filename_path = f'{output_filename}/grupo_x{x}/yappy_delete_com.csv'
        os.makedirs(os.path.dirname(filename_path), exist_ok= True)

        with open(filename_path, 'w', newline='') as csvfile:

            csvwriter = csv.writer(csvfile, delimiter= ',', quoting = csv.QUOTE_NONE, escapechar='\\')

            if(x < archivos_total):
                csvwriter.writerows(lista_depuracion[indice_min:(indice_max-1)])
            else:
                csvwriter.writerows(lista_depuracion[indice_min:(filas_total-1)])

            csvwriter = csv.writer(csvfile, delimiter= ',', quoting = csv.QUOTE_NONE, escapechar='\\', lineterminator= "")

            if(x < archivos_total):
                csvwriter.writerows(lista_depuracion[indice_max-1])
            else:
                csvwriter.writerows(lista_depuracion[filas_total-1])
        
        indice_min +=15
        indice_max +=15

    # Crear el archivo ZIP
    shutil.make_archive(output_filename, 'zip', output_filename)

    with open(os.path.join(output_filename, "incompletos_csv.txt"), "w") as txt_file:
        txt_file.write("INOMPLETOS PARA CSV")
        for line in lista_incompletos:
            txt_file.write("\n" + str(line))

def creacion_query_uuids(lista_id_admin, lista_id_comercio, nombre_excel, lista_incompletos):

    carpeta = f'queries_depuracion_{nombre_excel}'
    nombre_archivo = "BusquedaUUIDs.sql"
    ruta_completa = os.path.join(carpeta, nombre_archivo)

    os.makedirs(carpeta, exist_ok=True)

    admin_tupla = tuple(lista_id_admin)
    comercio_tupla = tuple(lista_id_comercio)

    query_admin = (f' Select * From Where In {admin_tupla}')
    query_comercio = (f' Select * From Where In {comercio_tupla}')

    #with open(ruta_completa, "w") as f: 
    #Linea 85


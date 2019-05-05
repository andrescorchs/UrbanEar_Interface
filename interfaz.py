#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from tkinter import *
from tkinter import ttk, font, messagebox, filedialog
import tkSnack

opt = {
        'filetypes' : [('All','*.npy *.wav'),('Numpy','*.npy'),('WAV','*.wav')],
#        'initialdir' :                             directorio inicial para la busqueda
        }
opt_h = {
        'filetypes' : [('Numpy','*.npy')],
        'initialdir' : [('./ArchivosSPL')]
        }

from yaml import load, dump
try:
    from yaml import CLoader as Loader, CDumper as Dumper
except ImportError:
    from yaml import Loader, Dumper

import pylab as plt
import numpy as np
from matplotlib.colors import LogNorm
from matplotlib.ticker import LogFormatterMathtext

from threading import Timer

from subprocess import run, PIPE

import paramiko

import os

##### PARAMETROS DE LA CONEXION #####
HOSTE = '164.73.38.190'
HOSTW = '192.168.127.1'
PUERTO = 22
USUARIO = 'pi'
CONTRASENA = 'm4r10k4rt'
datos_e = dict(hostname=HOSTE, port=PUERTO, username=USUARIO, password=CONTRASENA)
datos_w = dict(hostname=HOSTW, port=PUERTO, username=USUARIO, password=CONTRASENA)
datos = None

#### GENERO CARPETAS PARA DATOS ####
os.system("mkdir Audios > /dev/null")
os.system("mkdir ArchivosSPL > /dev/null")
os.system("mkdir ArchivosMel > /dev/null")

#### SERVIDOR ####
SERVER_TIME = 30
server = None

class Urbanear():
    def __init__(self):
        self.raiz = Tk()
        self.raiz.geometry('500x450')
        self.raiz.resizable(0,0)
        self.raiz.configure(bg='beige')
        self.raiz.title('Urbanear')
        self.fuente = font.Font(weight='bold')
        self.raiz.option_add('*tearOff', False)  # Deshabilita submenús flotantes

        logo = PhotoImage(file='Imagenes/logo.png')

        self.raiz.logo = ttk.Label(self.raiz, image=logo,
                                 anchor="center", background='beige')

        self.message = StringVar()
        mensaje = "Servidor detenido"
        self.message.set(mensaje)

        self.escala = IntVar()
        self.escala.set(0)

        self.temp = IntVar()
        self.temp.set(0)

        self.spl = IntVar()
        self.spl.set(0)

        self.conn = IntVar()
        self.conn.set(0)

        self.graf = IntVar()
        self.graf.set(0)

        barramenu = Menu(self.raiz)
        self.raiz['menu'] = barramenu

        self.menu1 = Menu(barramenu)
        self.menu2 = Menu(barramenu)
        self.menu4 = Menu(barramenu)
        self.menu5 = Menu(barramenu)
        barramenu.add_cascade(menu=self.menu1, label='Servidor')
        barramenu.add_cascade(menu=self.menu2, label='Nodo')
        barramenu.add_cascade(menu=self.menu4, label='BandasMel')
        barramenu.add_cascade(menu=self.menu5, label='SPL')

        self.menu1.add_radiobutton(label='Wifi',
                          variable=self.conn,
                          value=0)

        self.menu1.add_radiobutton(label='Ethernet',
                          variable=self.conn,
                          value=1)

        self.menu1.add_separator()

        self.menu1.add_command(label='Comenzar',
                          command=self.runServer,
                          state="normal", underline=0)

        self.menu1.add_command(label='Detener',
                          command=self.stopServer,
                          state="disabled", underline=0)

        self.menu2.add_command(label='Configuracion Actual',
                          command=self.configActual,
                          state="normal", underline=0)

        self.menu2.add_command(label='Configurar',
                          command=self.setConfig,
                          state="normal", underline=0)


        self.menu2.add_command(label='Reiniciar',
                          command=self.reiniciar,
                          state="normal", underline=0)


        self.menu4.add_radiobutton(label='Escala lineal',
                          variable=self.escala,
                          value=0)
        self.menu4.add_radiobutton(label='Escala mel',
                          variable=self.escala,
                          value=1)

        self.menu5.add_radiobutton(label='Particular',
                          variable=self.spl,
                          value=0)

        self.menu5.add_radiobutton(label='Historico',
                          variable=self.spl,
                          value=1)

        self.menu5.add_separator()


        self.menu5.add_radiobutton(label='Puntos',
                          variable=self.graf,
                          value=0)

        self.menu5.add_radiobutton(label='Barras',
                          variable=self.graf,
                          value=1)

        self.raiz.logo.pack(side=TOP, fill=BOTH, expand=True,
                          padx=10, pady=5)

        self.barraest = Label(self.raiz, text=self.message.get(),
                              bd=1, relief=SUNKEN,  anchor=W)
        self.barraest.pack(side=BOTTOM, fill=X)

        self.bsalir = ttk.Button(self.raiz, text='Salir', command=self.cerrar)
        self.bsalir.pack(side=BOTTOM)

        self.bdatos = ttk.Button(self.raiz, text='Mostrar Datos', command=self.showData)
        self.bdatos.pack(side=BOTTOM)

        self.bdatos.focus_set()

        self.raiz.mainloop()

    def cerrar(self):
        try:
            plt.close()
            threading.exit()
        except:
            no_figuras = True
        if server != None:
            server.cancel()
        self.raiz.destroy()

    def reiniciar(self):
        global datos
        if self.conn.get() == 1:
            global datos_e
            datos = datos_e
        else:
            global datos_w
            datos = datos_w
        response = os.system("ping -c 3 " + datos['hostname'] + " > /dev/null")
        if response != 0:
            messagebox.showerror("Error", "Imposible de conectar con el dispositivo.")
            return
        seguro = messagebox.askyesno("Reinicio","¿Seguro que desea reiniciar el nodo?")
        if seguro:
            command("sudo reboot", datos)


    def runServer(self):
        global datos
        if self.conn.get() == 1:
            global datos_e
            datos = datos_e
        else:
            global datos_w
            datos = datos_w
#        response = os.system("ping -c 3 " + datos['hostname'] + " > /dev/null")
#        if response != 0:
#            messagebox.showerror("Error", "Imposible de conectar con el dispositivo.")
#            return
        setear = messagebox.askyesno("Consulta", "El servidor consulta cada " + str(SERVER_TIME) + " segundos. Esta de acuerdo?" )
        if not setear:
            self.timer = Toplevel()
            self.timer.geometry('300x150')
            self.timer.resizable(0,0)
            self.timer.configure(bg='white')
            self.timer.title('Tiempo de consulta')
            self.time = IntVar(value=SERVER_TIME)

            self.timer.etiq = ttk.Label(self.timer,
                               text="Ingrese el nuevo intervalo de consulta\n en segundos:", justify=CENTER)
            self.timer.tiempo = ttk.Entry(self.timer, textvariable=self.time,
                              width=10, justify=CENTER)
            self.timer.b = ttk.Button(self.timer, text='Aplicar',
                               command=self.aplicar_tiempo)
            self.timer.etiq.pack(side=TOP, fill=X, expand=True,
                            padx=25, pady=5)
            self.timer.tiempo.pack(side=TOP, fill=X, expand=True,
                            padx=25, pady=5)
            self.timer.b.pack(side=TOP, fill=X, expand=True,
                            padx=25, pady=5)
            self.timer.transient(master=self.raiz)
            self.timer.grab_set()
            self.raiz.wait_window(self.timer)

        global server
        server = Timer(SERVER_TIME, getFiles)
        server.start()
        self.menu1.entryconfig("Detener", state="normal")
        self.menu1.entryconfig("Comenzar", state="disabled")
        messagebox.showinfo("Info", "El servidor fue iniciado.")
        self.message.set("Servidor iniciado")
        self.barraest.config(text=self.message.get())

    def aplicar_tiempo(self):
        aux = self.time.get()
        if aux == None or aux <= 0:
            messagebox.showerror("Error", "Debe ingresarse un entero positivo")
        else:
            global SERVER_TIME
            SERVER_TIME = aux
        self.timer.destroy()

    def stopServer(self):
        global server
        server.cancel()
        server = None
        self.menu1.entryconfig("Comenzar", state="normal")
        self.menu1.entryconfig("Detener", state="disabled")
        self.message.set("Servidor detenido")
        self.barraest.config(text=self.message.get())
        messagebox.showinfo("Info", "El servidor fue detenido.")

    def showData(self):
        archivo = filedialog.askopenfile(**opt)
        if archivo == None:
            return 0
        indicador = archivo.name.rfind('SPL')
        if self.spl.get() and indicador != -1:
            messagebox.showinfo("Info", "Seleccionado el archivo correspondiente al inicio\n"
            + "seleccione el archivo correspondiente al final del intervalo de tiempo.")
            archivo_f = filedialog.askopenfile(**opt_h)
            if(archivo.name >= archivo_f.name):
                messagebox.showerror("Error", "Debe seleccionar un archivo posterior al inicial.")
                return
            directorio = run(["ls ArchivosSPL"], shell=True, stdout=PIPE).stdout
            archivos = directorio.strip().decode('ascii')
            inicio_s = archivo.name.split('/')[9]
            fin_s = archivo_f.name.split('/')[9]
            i_i = archivos.find(inicio_s)
            f_i = archivos.find(fin_s)
            vector = np.load('./ArchivosSPL/' + archivos[i_i:i_i+23])
            timestamp = []
            timestamp.append(archivos[i_i:i_i+15])
            i_i += 24
            f_i += 24
            for i in range(i_i, f_i, 24):
                timestamp.append(archivos[i:i+15])
                aux = np.load('./ArchivosSPL/' + archivos[i:i+23])
                vector = np.concatenate([vector, aux])
            plotspl_h(vector, timestamp)
        else:
            if indicador != -1:
                mostrar = np.load(archivo.name)
                arch = archivo.name
                seg = arch[indicador-3:indicador-1]
                min = arch[indicador-5:indicador-3]
                hora = arch[indicador-7:indicador-5]
                dia = arch[indicador-10:indicador-8]
                mes = arch[indicador-12:indicador-10]
                anio = arch[indicador-16:indicador-12]
                titulo = dia + "/" + mes + "/" + anio + " a las " + hora + ":" + min + ":" + seg
                plotspl(mostrar, self.graf.get(), titulo=titulo)
            else:
                indicador = archivo.name.rfind('Mel')
                if indicador != -1:
                    mostrar = np.load(archivo.name)
                    arch = archivo.name
                    seg = arch[indicador-3:indicador-1]
                    min = arch[indicador-5:indicador-3]
                    hora = arch[indicador-7:indicador-5]
                    dia = arch[indicador-10:indicador-8]
                    mes = arch[indicador-12:indicador-10]
                    anio = arch[indicador-16:indicador-12]
                    titulo = dia + "/" + mes + "/" + anio + " a las " + hora + ":" + min + ":" + seg
                    aux = levantar_configuracion()
                    plotmel(mostrar, self.escala.get(), titulo=titulo, duracion=aux['duration'],freclow=aux['freclow'],frechigh=aux['frechigh'],nfilt=aux['nfilt'])
                else:
                    self.reproductor(archivo.name)

    def reproductor(self, path):
        self.reprod = Toplevel()
        self.reprod.geometry("250x200")
        self.reprod.resizable(0,0)
        self.reprod.configure(bg='white')
        self.reprod.title('Reproductor')

        tkSnack.initializeSnack(self.reprod)
        self.snd = tkSnack.Sound()
        logo = PhotoImage(file='Imagenes/audio_opt.png')

        self.reprod.logo = ttk.Label(self.reprod, image=logo,
                                 anchor="center", background='white')
        self.snd.read(path)
        self.player = False
        min = int(self.snd.length(unit="SECONDS")/60)
        sec = self.snd.length(unit="SECONDS")%60
        if (min<10):
            min_str = "0" + str(min)
        else:
            min_str = str(min)
        if (sec<10):
            sec_str = "0" + str(sec)
        else:
            sec_str = str(sec)
        tiempo = "duracion " + min_str + ":" + sec_str
        self.reprod.duracion = Label(self.reprod, text=tiempo,
                                bg='white')
        self.reprod.duracion.pack(side=TOP)
        self.reprod.logo.pack(side=TOP)

        self.reprod.play = ttk.Button(self.reprod, text='Play', command=self.play)
        self.reprod.play.place(x=1,y=130)
        self.reprod.pause = ttk.Button(self.reprod, text='Pause', command=self.pause)
        self.reprod.pause.place(x=83,y=130)
        self.reprod.stop = ttk.Button(self.reprod, text='Stopped', command=self.stop)
        self.reprod.stop.place(x=166,y=130)
        self.reprod.exit = ttk.Button(self.reprod, text='Exit', command=self.exit)
        self.reprod.exit.place(x=83,y=170)


        self.reprod.transient(master=self.raiz)
        self.reprod.grab_set()

        self.raiz.wait_window(self.reprod)

    def play(self):
        if not(self.player):
            self.snd.play(command=self.stop)
            self.player = True
            self.reprod.play.configure(text="Playing")
            self.reprod.pause.configure(text="Pause")
            self.reprod.stop.configure(text="Stop")


    def pause(self):
        if(self.player):
            self.snd.pause()
            self.player = False
            self.reprod.play.configure(text="Resume")
            self.reprod.pause.configure(text="Paused")
            self.reprod.stop.configure(text="Stop")

    def stop(self):
        self.snd.stop()
        self.player = False
        self.reprod.play.configure(text="Play")
        self.reprod.pause.configure(text="Pause")
        self.reprod.stop.configure(text="Stopped")

    def exit(self):
        self.snd.stop()
        self.reprod.destroy()

    def setConfig(self):
        self.config = Toplevel()
        self.config.geometry('450x620')
        self.config.resizable(0,0)
        self.config.configure(bg='white')
        self.config.title('Configurar')
        self.canvas = Canvas(self.config, bg='white')
        self.scrollbar = Scrollbar(self.config, orient='vertical',command=self.canvas.yview)

        frame = Frame(self.canvas, bg='white')

        self.fs = IntVar(value=44100)
        self.ncomp   = IntVar(value=256)
        self.duration = IntVar(value=10)
        self.delay = IntVar(value=40)
        self.saveaudio = BooleanVar()
        self.cantarchaudios = IntVar(value=10)
        self.nfilt = IntVar(value=60)
        self.normmel = BooleanVar()
        self.freclow = IntVar(value=0)
        self.frechigh = IntVar(value=22050)
        self.cantarchmel = IntVar(value=10)
        self.cantspl = IntVar(value=60)
        self.cantarchspl = IntVar(value=10)
        self.norm = BooleanVar()
        self.preenf = BooleanVar()
        self.alpha = DoubleVar(value=0.97)
        self.fsize = DoubleVar(value=0.025)
        self.fstride = DoubleVar(value=0.0125)
        self.ventana = StringVar(value="hann")
        self.nfft = IntVar(value=0)
        self.default = BooleanVar()
        self.calcMel = BooleanVar()
        self.calcSPL = BooleanVar()

        self.config.etiq_gral = ttk.Label(frame,
                               text="Parametros generales:", font=font.Font(family="Helvetica", size=12, weight="bold"))
        self.config.etiq1 = ttk.Label(frame,
                               text="Frecuencia de muestreo (Hz):")
        self.config.fs = ttk.Combobox(frame, state="readonly", textvariable=self.fs,
                              width=10)
        #opciones
        self.config.fs["values"] = ["44100", "32000", "22050", "16000", "8000"]
        self.config.etiq2 = ttk.Label(frame,
                               text="Duracion del audio (s):")
        self.config.duration = ttk.Entry(frame, textvariable=self.duration,
                              width=10)
        self.config.etiq3 = ttk.Label(frame,
                               text="Intervalo entre inicio de grabaciones (s):")
        self.config.delay = ttk.Entry(frame, textvariable=self.delay,
                              width=10)
        self.config.etiq_mel = ttk.Label(frame,
                               text="Parametros para bandas mel:", font=font.Font(family="Helvetica", size=12, weight="bold"))
        self.config.etiq4 = ttk.Label(frame,
                               text="Cantidad de bandas mel:")
        self.config.nfilt = ttk.Entry(frame, textvariable=self.nfilt,
                              width=10)
        self.config.etiq5 = ttk.Label(frame,
                               text="Tipo de normalizacion:")
        self.config.normmel2 = ttk.Radiobutton(frame, text='Area',
                                variable=self.normmel, value=True)
        self.config.normmel3 = ttk.Radiobutton(frame, text='Amplitud',
                                variable=self.normmel, value=False)

        self.config.etiq6 = ttk.Label(frame,
                                text="Cantidad de archivos Mel a almacenar en el nodo:")
        self.config.archmel = ttk.Entry(frame, textvariable=self.cantarchmel,
                                width=10)

        self.config.etiq7 = ttk.Label(frame,
                                text="Frecuencia inferior (Hz):")
        self.config.freclow = ttk.Entry(frame, textvariable=self.freclow,
                                width=10)

        self.config.etiq8 = ttk.Label(frame,
                                text="Frecuencia superior (Hz):")
        self.config.frechigh = ttk.Entry(frame, textvariable=self.frechigh,
                                width=10)

        self.config.etiq_spl = ttk.Label(frame,
                               text="Parametros para SPL:", font=font.Font(family="Helvetica", size=12, weight="bold"))
        self.config.etiq9 = ttk.Label(frame,
                               text="Cantidad de puntos de spl:")
        self.config.cantspl = ttk.Entry(frame, textvariable=self.cantspl,
                              width=10)

        self.config.etiq10 = ttk.Label(frame,
                               text="Cantidad de archivos de spl a almacenar en el nodo:")
        self.config.cantarchspl = ttk.Entry(frame, textvariable=self.cantarchspl,
                              width=10)

        self.config.default = ttk.Checkbutton(frame, text='Guardar como configuracion predeterminada',
                                      variable=self.default,
                                      onvalue=True, offvalue=False)
        self.config.saveaudio = ttk.Checkbutton(frame, text='Guardar archivos de audio en el nodo',
                                      variable=self.saveaudio,
                                      onvalue=True, offvalue=False)
        self.config.etiq11 = ttk.Label(frame,
                               text="Numero de puntos para interpolar filtro:")
        self.config.ncomp = ttk.Entry(frame, textvariable=self.ncomp,
                              width=10)
        self.config.etiq12 = ttk.Label(frame,
                               text="Cantidad de archivos de audio a almacenar en el nodo:")
        self.config.cantarchaudios = ttk.Entry(frame, textvariable=self.cantarchaudios,
                              width=10)
        self.config.etiq17 = ttk.Label(frame,
                               text="Tipo de ventana a utilizar:")
        self.config.ventana = ttk.Combobox(frame, state="readonly", textvariable=self.ventana,
                              width=10)
        #opciones
        self.config.ventana["values"] = ["hann", "boxcar", "triang", "blackman", "hamming", "bartlett", "flattop", "parzen", "bohman", "blackmanharris", "nuttall", "barthann"]

        self.config.preenf = ttk.Checkbutton(frame, text='Aplicar filtro de pre-enfasis al audio',
                                      variable=self.preenf,
                                      onvalue=True, offvalue=False)
        self.config.etiq13 = ttk.Label(frame,
                               text="Coeficiente del filtro de pre-enfasis:")
        self.config.alpha = ttk.Entry(frame, textvariable=self.alpha,
                              width=10)
        self.config.etiq14 = ttk.Label(frame,
                               text="Tamaño de ventana (ms):")
        self.config.fsize = ttk.Entry(frame, textvariable=self.fsize,
                              width=10)
        self.config.etiq15 = ttk.Label(frame,
                               text="Cada cuanto comienza una ventana nueva (ms):")
        self.config.fstride = ttk.Entry(frame, textvariable=self.fstride,
                              width=10)
        self.config.etiq16 = ttk.Label(frame,
                               text="Cantidad de ceros a rellenar:")
        self.config.nfft = ttk.Entry(frame, textvariable=self.nfft,
                              width=10)
        self.config.calcMel = ttk.Checkbutton(frame, text='Calcular bandas Mel',
                                      variable=self.calcMel,
                                      onvalue=True, offvalue=False)
        self.config.calcSPL = ttk.Checkbutton(frame, text='Calcular SPL',
                                      variable=self.calcSPL,
                                      onvalue=True, offvalue=False)

        self.config.etiq_gral.pack(side=TOP, fill=BOTH, expand=True,
                        padx=10, pady=5)
        self.config.etiq1.pack(side=TOP, fill=BOTH, expand=True,
                        padx=20, pady=5)
        self.config.fs.pack(side=TOP, fill=X, expand=True,
                        padx=25, pady=5)
        self.config.etiq2.pack(side=TOP, fill=BOTH, expand=True,
                        padx=20, pady=5)
        self.config.duration.pack(side=TOP, fill=X, expand=True,
                        padx=25, pady=5)
        self.config.etiq3.pack(side=TOP, fill=BOTH, expand=True,
                        padx=20, pady=5)
        self.config.delay.pack(side=TOP, fill=X, expand=True,
                        padx=25, pady=5)
        self.config.etiq11.pack(side=TOP, fill=BOTH, expand=True,
                        padx=20, pady=5)
        self.config.ncomp.pack(side=TOP, fill=X, expand=True,
                        padx=25, pady=5)
        self.config.saveaudio.pack(side=TOP, fill=X, expand=True,
                         padx=20, pady=5)
        self.config.etiq12.pack(side=TOP, fill=BOTH, expand=True,
                        padx=20, pady=5)
        self.config.cantarchaudios.pack(side=TOP, fill=X, expand=True,
                        padx=25, pady=5)
        self.config.default.pack(side=TOP, fill=X, expand=True,
                         padx=20, pady=5)
        self.config.etiq_mel.pack(side=TOP, fill=BOTH, expand=True,
                        padx=10, pady=5)
        self.config.calcMel.pack(side=TOP, fill=X, expand=True,
                        padx=20, pady=5)
        self.config.etiq4.pack(side=TOP, fill=BOTH, expand=True,
                        padx=20, pady=5)
        self.config.nfilt.pack(side=TOP, fill=X, expand=True,
                        padx=25, pady=5)
        self.config.preenf.pack(side=TOP, fill=X, expand=True,
                        padx=20, pady=5)
        self.config.etiq13.pack(side=TOP, fill=BOTH, expand=True,
                        padx=20, pady=5)
        self.config.alpha.pack(side=TOP, fill=X, expand=True,
                        padx=25, pady=5)
        self.config.etiq17.pack(side=TOP, fill=BOTH, expand=True,
                        padx=20, pady=5)
        self.config.ventana.pack(side=TOP, fill=BOTH, expand=True,
                        padx=25, pady=5)
        self.config.etiq5.pack(side=TOP, fill=X, expand=True,
                        padx=20, pady=5)
        self.config.normmel2.pack(side=TOP, fill=X, expand=True,
                        padx=25, pady=5)
        self.config.normmel3.pack(side=TOP, fill=X, expand=True,
                        padx=25, pady=5)
        self.config.etiq14.pack(side=TOP, fill=BOTH, expand=True,
                        padx=20, pady=5)
        self.config.fsize.pack(side=TOP, fill=X, expand=True,
                        padx=25, pady=5)
        self.config.etiq15.pack(side=TOP, fill=BOTH, expand=True,
                        padx=20, pady=5)
        self.config.fstride.pack(side=TOP, fill=X, expand=True,
                        padx=25, pady=5)
        self.config.etiq16.pack(side=TOP, fill=BOTH, expand=True,
                        padx=20, pady=5)
        self.config.nfft.pack(side=TOP, fill=X, expand=True,
                        padx=25, pady=5)
        self.config.etiq7.pack(side=TOP, fill=X, expand=True,
                        padx=20, pady=5)
        self.config.freclow.pack(side=TOP, fill=X, expand=True,
                        padx=25, pady=5)
        self.config.etiq8.pack(side=TOP, fill=X, expand=True,
                        padx=20, pady=5)
        self.config.frechigh.pack(side=TOP, fill=X, expand=True,
                        padx=25, pady=5)
        self.config.etiq6.pack(side=TOP, fill=X, expand=True,
                        padx=20, pady=5)
        self.config.archmel.pack(side=TOP, fill=X, expand=True,
                        padx=25, pady=5)
        self.config.etiq_spl.pack(side=TOP, fill=X, expand=True,
                        padx=10, pady=5)
        self.config.calcSPL.pack(side=TOP, fill=X, expand=True,
                        padx=20, pady=5)
        self.config.etiq9.pack(side=TOP, fill=X, expand=True,
                        padx=20, pady=5)
        self.config.cantspl.pack(side=TOP, fill=X, expand=True,
                        padx=25, pady=5)
        self.config.etiq10.pack(side=TOP, fill=X, expand=True,
                        padx=20, pady=5)
        self.config.cantarchspl.pack(side=TOP, fill=X, expand=True,
                        padx=25, pady=5)

        boton1 = ttk.Button(frame, text='Cerrar',
                           command=self.config.destroy)
        boton1.pack(side=RIGHT)

        boton2 = ttk.Button(frame, text='Aplicar',
                           command=self.aplicar)
        boton2.pack(side=LEFT)

        self.canvas.create_window(0, 0, anchor='nw', window=frame)

        self.canvas.update_idletasks()

        self.canvas.bind("<Button-4>", self._on_mousewheel)
        self.canvas.bind("<Button-5>", self._on_mousewheel)
        self.canvas.configure(scrollregion=self.canvas.bbox('all'),
                 yscrollcommand=self.scrollbar.set)

        self.canvas.pack(fill='both', expand=True, side=LEFT)
        self.scrollbar.pack(fill='y', side=RIGHT)

        self.config.transient(master=self.raiz)
        self.config.grab_set()

        self.raiz.wait_window(self.config)

#bajar la barra con el mouse
    def _on_mousewheel(self, event):
        if event.num == 4:
            self.canvas.yview('scroll', -1, 'units')
        elif event.num == 5:
            self.canvas.yview('scroll', 1, 'units')

    def aplicar(self):
        global datos
        if self.conn.get() == 1:
            global datos_e
            datos = datos_e
        else:
            global datos_w
            datos = datos_w
        response = os.system("ping -c 3 " + datos['hostname'] + " > /dev/null")
        if response != 0:
            messagebox.showerror("Error", "Imposible de conectar con el dispositivo.")
            return
        #chequeo condiciones
        try:
            if self.ncomp.get() < 0:
                messagebox.showerror("Error", "Inconsistencia en los parametros de configuracion.")
                return
            if self.duration.get() <= 0:
                messagebox.showerror("Error", "Inconsistencia en los parametros de configuracion.")
                return
            if self.delay.get() < 0:
                messagebox.showerror("Error", "Inconsistencia en los parametros de configuracion.")
                return
            if self.cantarchaudios.get() < 0 and self.saveaudio.get():
                messagebox.showerror("Error", "Inconsistencia en los parametros de configuracion.")
                return
            if self.nfilt.get() <= 0:
                messagebox.showerror("Error", "Inconsistencia en los parametros de configuracion.")
                return
            if self.freclow.get() < 0 or self.freclow.get() >= self.frechigh.get():
                messagebox.showerror("Error", "Inconsistencia en los parametros de configuracion.")
                return
            if self.frechigh.get() > (self.fs.get()/2):
                messagebox.showerror("Error", "Inconsistencia en los parametros de configuracion.")
                return
            if self.cantarchmel.get() < 0:
                messagebox.showerror("Error", "Inconsistencia en los parametros de configuracion.")
                return
            if self.cantspl.get() < 0:
                messagebox.showerror("Error", "Inconsistencia en los parametros de configuracion.")
                return
            if self.cantarchspl.get() < 0:
                messagebox.showerror("Error", "Inconsistencia en los parametros de configuracion.")
                return
            if self.alpha.get() <= 0 and self.preenf.get():
                messagebox.showerror("Error", "Inconsistencia en los parametros de configuracion.")
                return
            if self.fsize.get() < 0:
                messagebox.showerror("Error", "Inconsistencia en los parametros de configuracion.")
                return
            if self.fstride.get() < 0:
                messagebox.showerror("Error", "Inconsistencia en los parametros de configuracion.")
                return
            if self.nfft.get() < 0:
                messagebox.showerror("Error", "Inconsistencia en los parametros de configuracion.")
                return
        except Exception:
            messagebox.showerror("Error", "Todos los campos deben ser llenados.")
            return
        getConfig()
        recalcular = False
        aux = levantar_configuracion()
        if aux['fs'] != self.fs.get():
            recalcular = True
        aux['fs'] = self.fs.get()
        if aux['ncomp'] != self.ncomp.get():
            recalcular = True
        aux['ncomp'] = self.ncomp.get()
        aux['duration'] = self.duration.get()
        aux['save_audio'] = self.saveaudio.get()
        aux['cantAudios'] = self.cantarchaudios.get()
        aux['calcMel'] = self.calcMel.get()
        aux['nfilt'] = self.nfilt.get()
        aux['pre_enf'] = self.preenf.get()
        aux['alpha'] = self.alpha.get()
        aux['f_size'] = self.fsize.get()
        aux['f_stride'] = self.fstride.get()
        aux['ventana'] = self.ventana.get()
        aux['normMel'] = self.normmel.get()
        aux['freclow'] = self.freclow.get()
        aux['frechigh'] = self.frechigh.get()
        aux['nfft'] = self.nfft.get()
        aux['CantArchMel'] = self.cantarchmel.get()
        aux['calcSPL'] = self.calcSPL.get()
        aux['cant_SPL'] = self.cantspl.get()
        aux['CantArchSPL'] = self.cantarchspl.get()
        sacar_configuracion(aux)
        putConfig(self.default.get(), recalcular)
        self.config.destroy()

    def configActual(self):
        global datos
        if self.conn.get() == 1:
            global datos_e
            datos = datos_e
        else:
            global datos_w
            datos = datos_w
        response = os.system("ping -c 3 " + datos['hostname'] + " > /dev/null")
        if response != 0:
            messagebox.showerror("Error", "Imposible de conectar con el dispositivo.")
            return
        getConfig()
        temp = levantar_configuracion()
        self.dialogo = Toplevel()
        self.dialogo.geometry('480x460')
        self.dialogo.configure(bg='white')
        self.dialogo.title('Configuracion Actual')

        self.info = Text(self.dialogo, width=55, height=23)
        self.info.pack(side=TOP)

        # Borra el contenido que tenga en un momento dado
        # la caja de texto
        self.info.delete("1.0", END)

        # Obtiene información de la configuracion:
        info1 = str(temp['fs'])
        info3 = str(temp['ncomp'])
        info4 = str(temp['duration'])
        info6 = str(temp['save_audio'])
        info5 = str(temp['delay'])
        info7 = str(temp['cantAudios'])
        info9 = str(temp['nfilt'])
        info10 = str(temp['pre_enf'])
        info11 = str(temp['alpha'])
        info12 = str(temp['f_size'])
        info13 = str(temp['f_stride'])
        info14 = str(temp['ventana'])
        info15 = str(temp['normMel'])
        info16 = str(temp['freclow'])
        info17 = str(temp['frechigh'])
        info18 = str(temp['nfft'])
        info19 = str(temp['CantArchMel'])
        info20 = str(temp['calcMel'])
        info21 = str(temp['cant_SPL'])
        info22 = str(temp['CantArchSPL'])
        info23 = str(temp['calcSPL'])

        # Construye una cadena de texto con toda la
        # información obtenida:

        texto_info = "frecuancia de muestreo: " + info1 + "Hz\n"
        texto_info += "numero de puntos para interpolar: " + info3 + "\n"
        texto_info += "duracion del audio grabado: " + info4 + "s\n"
        texto_info += "intervalo entre grabaciones: " + info5 + "s\n"
        texto_info += "se guarda el audio grabado: " + info6 + "\n"
        texto_info += "cantidad de audios a guardar en memoria: " + info7 + "\n"
        texto_info += "cantidad de bandas mel a calcular: " + info9 + "\n"
        texto_info += "aplicar un pre enfasis al audio: " + info10 + "\n"
        texto_info += "coeficiente para el filtro de pre enfasis: " + info11 + "\n"
        texto_info += "tamaño de ventana: " + info12 + "ms\n"
        texto_info += "cada cuanto comienza una ventana nueva: " + info13 + "ms\n"
        texto_info += "tipo de ventana a aplicar: " + info14 + "\n"
        texto_info += "normalizar las bandas mel: " + info15 + "\n"
        texto_info += "frecuencia inferior para las bandas mel: " + info16 + "\n"
        texto_info += "frecuencia superior para las bandas mel: " + info17 + "\n"
        texto_info += "cantidad de ceros a agregar al audio: " + info18 + "\n"
        texto_info += "cantidad de archivos a guardar de bandas mel: " + info19 + "\n"
        texto_info += "se desean calcular bandas mel: " + info20 + "\n"
        texto_info += "cantidad de valores de spl a tomar del audio: " + info21 + "\n"
        texto_info += "cantidad de archivos de spl a guardar: " + info22 + "\n"
        texto_info += "se desea calcular SPL: " + info23 + "\n"

        # Inserta la información en la caja de texto:

        boton = ttk.Button(self.dialogo, text='Cerrar',
                           command=self.dialogo.destroy)
        boton.pack(side=BOTTOM)

        self.dialogo.transient(master=self.raiz)
        self.dialogo.grab_set()

        self.info.insert("1.0", texto_info)
        self.raiz.wait_window(self.dialogo)

def levantar_configuracion():
    f = open('./config.yaml', 'r')
    document = f.read()
    f.close()
    return load(document, Loader=Loader)

def sacar_configuracion(config):
    f = open('./config.yaml', 'w')
    dump(config, f, Dumper=Dumper, default_flow_style=False)
    f.close()


############## Funciones de Ploteo #######################
def plotmel(Zdb, escala, titulo="Mel" ,duracion=10,freclow=0,frechigh=22050,nfilt=60):
    low_freq_mel = (2595*np.log10(1+(freclow/700)))
    high_freq_mel = (2595*np.log10(1+(frechigh/700)))
    mel_points = np.linspace(low_freq_mel, high_freq_mel, nfilt+2)
    hz_points = 700*(10**(mel_points/2595)-1)
    hz_points = hz_points[1:-1]

    plt.clf()
    if escala:
        im3 = plt.imshow(Zdb, origin='lower', aspect='auto', extent=[0, duracion, 0, nfilt], cmap='plasma', interpolation='none')
        plt.ylabel('mel (log(Hz))')
    else:
        indt = Zdb.shape[1]
        tmel = np.arange(0,indt)*duracion/(indt-1)
        T, F = np.meshgrid(tmel,hz_points)
        im3 = plt.pcolormesh(T,F,Zdb,cmap='plasma')
        plt.yscale('log')
        plt.ylabel('frecuencia (Hz)')
    plt.xlabel('tiempo (s)')
    plt.title(titulo)
    plt.show()


def plotspl(spl, graf, titulo='SPL'):
    indice = np.arange(spl.shape[1])
    bar_larg = 0.5
    transp = 0.6
    plt.clf()
    if graf:
        for i in indice:
            plt.bar(indice[i], spl[0][i], bar_larg, alpha=transp, color='b')
            plt.bar(indice[i] + bar_larg, spl[1][i], bar_larg, alpha=transp, color='g')
        plt.xticks(indice + bar_larg/2, (indice+1))
    else:
        plt.plot(indice, spl[0], 'b*')
        plt.plot(indice, spl[1], 'g*')
        plt.xticks(indice, (indice+1))
    plt.xlabel('Medida')
    plt.ylabel('SPL (dB)')
    plt.title(titulo)
    plt.legend(('Curva A', 'Curva C'), loc=1)
    plt.tight_layout()
    plt.show()

def plotspl_h(spl, time, titulo='Historial SPL'):
    indice = np.arange(len(time))
    plt.clf()
    curva_a = []
    curva_c = []
    ejex = []
    ticks = []
    acumulado = 0
    for i in indice:
        curva_a = np.append(curva_a, spl[i*2])
        curva_c = np.append(curva_c, spl[(i*2)+1])
        ejex.append(time[i])
        ticks.append(acumulado)
        acumulado += spl[i*2].shape[0]
    plt.plot(curva_a, 'b*')
    plt.plot(curva_c, 'g*')
    plt.xticks(ticks, ejex, rotation='vertical')
    plt.xlabel('Fechas')
    plt.ylabel('SPL (dB)')
    plt.title(titulo)
    plt.legend(('Curva A', 'Curva C'), loc=1)
    plt.tight_layout()
    plt.show()
############## Funcion de Servidor #######################
def getFiles():
    ssh_client = paramiko.SSHClient()
    ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh_client.connect(**datos)


    sftp = ssh_client.open_sftp()
    # Descargando archivos
    ruta = "/home/pi/Repositorio_main/ArchivosMel"
    archivos = sftp.listdir(ruta)

    directorio = ((run(["pwd"], stdout=PIPE).stdout).strip()).decode('ascii')
    warning = False
    for archivo in archivos:
        archivo_remoto = "%(ruta)s/%(nombre)s" % dict(ruta=ruta, nombre=archivo)
        print ("Descargando: %s" % archivo_remoto)
        try:
            sftp.get(archivo_remoto, directorio + "/ArchivosMel/%s" % archivo)
            print ("copiado archivo %s." % archivo)
            sftp.remove(archivo_remoto)
        except:
            warning = True

    ruta = "/home/pi/Repositorio_main/ArchivosSPL"
    archivos = sftp.listdir(ruta)

    for archivo in archivos:
        archivo_remoto = "%(ruta)s/%(nombre)s" % dict(ruta=ruta, nombre=archivo)
        print ("Descargando: %s" % archivo_remoto)
        try:
            sftp.get(archivo_remoto, directorio + "/ArchivosSPL/%s" % archivo)
            print ("copiado archivo %s." % archivo)
            sftp.remove(archivo_remoto)
        except:
            warning = True

    ruta = "/home/pi/Repositorio_main/Audios"
    archivos = sftp.listdir(ruta)

    for archivo in archivos:
        archivo_remoto = "%(ruta)s/%(nombre)s" % dict(ruta=ruta, nombre=archivo)
        print ("Descargando: %s" % archivo_remoto)
        try:
            sftp.get(archivo_remoto, directorio + "/Audios/%s" % archivo)
            print ("copiado archivo %s." % archivo)
            sftp.remove(archivo_remoto)
        except:
            warning = True

    print("Termino de traer archivos.")

    sftp.close()
    ssh_client.close()

    if warning:
        messagebox.showwarning("Warning","Ocurrio un error al traer alguno de los archivos.")

    global server
    server = Timer(SERVER_TIME, getFiles)
    server.start()

def putConfig(default, recalc):
    ssh_client = paramiko.SSHClient()
    ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh_client.connect(**datos)

    sftp = ssh_client.open_sftp()

    directorio = ((run(["pwd"], stdout=PIPE).stdout).strip()).decode('ascii')
    ruta_origen = directorio + "/config.yaml"
    ruta = "/home/pi/Repositorio_main/config.yaml"
    try:
        sftp.put(ruta_origen,ruta)
        messagebox.showinfo("Info", "La configuracion fue cargada exitosamente.")
    except:
        messagebox.showerror("Error", "Fallo el envio de la configuracion.")

    if default:
        ruta = "/home/pi/Repositorio_main/config_default.yaml"
        try:
            sftp.put(ruta_origen,ruta)
            messagebox.showinfo("Info", "La configuracion por defecto fue cargada exitosamente.")
        except:
            messagebox.showerror("Error", "Fallo el envio de la configuracion por defecto.")

    sftp.close()
    ssh_client.close()

    if recalc:
        command("pkill -f main.py & nohup /home/pi/Repositorio_main/Scripts/supervisor.sh &",datos)

def getConfig():
    ssh_client = paramiko.SSHClient()
    ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh_client.connect(**datos)

    sftp = ssh_client.open_sftp()

    directorio = ((run(["pwd"], stdout=PIPE).stdout).strip()).decode('ascii')
    ruta_destino = directorio + "/config.yaml"
    ruta = "/home/pi/Repositorio_main/config.yaml"
    try:
        sftp.get(ruta, ruta_destino)
    except:
        messagebox.showerror("Error", "Fallo al intentar copiar la configuracion.")

    sftp.close()
    ssh_client.close()

def command(comando, datos):
    nbytes = 4096
    ssh_client = paramiko.Transport((datos['hostname'], datos['port']))
    ssh_client.connect(username=datos['username'], password=datos['password'])
    stdout_data = []
    stderr_data = []
    session = ssh_client.open_channel(kind='session')
    session.exec_command(comando)
    while True:
        if session.recv_ready():
            stdout_data.append(session.recv(nbytes))
        if session.recv_stderr_ready():
            stderr_data.append(session.recv_stderr(nbytes))
        if session.exit_status_ready():
            break

    if session.recv_exit_status() != 0:
        messagebox.showerror("Error", "Se detecto el siguiente error al modificar la configuracion: " + str(session.recv_exit_status()))

    session.close()
    ssh_client.close()



def main():
    app = Urbanear()
    return 0

if __name__ == '__main__':
    main()

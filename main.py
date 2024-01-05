import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from urllib.parse import urljoin
import locale
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from undetected_chromedriver import Chrome, ChromeOptions
import time
import re
import mensajes
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
import random
from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import ConversationHandler, CallbackContext
import ics
from itertools import islice
import wikipedia
from googlesearch import search



TOKEN = '6368195495:AAGTRPatrdbZKpKNx-KeetXO-S3LCPUMxk0'
SELECCIONAR_EVENTO = 1
wikipedia.set_lang("es")  


def fetch_top_search_results(query, num_results=10):
    search_results = search(query, num_results=num_results)
    return search_results

def obtener_info_eventos():
    base_url = 'https://www.esmadrid.com/'
    url = urljoin(base_url, 'que-hacer-semana-madrid')
    response = requests.get(url)
    num_eventos = 16
    eventos_lista = []
    borrar_primero=1
    if response.status_code == 200:
        html = response.content
        soup = BeautifulSoup(html, 'html.parser')
        eventos = soup.find_all('div', class_='ds-1col')
        for evento in eventos[:num_eventos]:
            titulo_element = evento.find('h3', class_='field-name-title-field')
            resumen_element = evento.find('div', class_='field-name-resumen')
            enlace_element = evento.find('a', href=True)

            if titulo_element and resumen_element:
                titulo = titulo_element.get_text(strip=True)
                resumen = resumen_element.get_text(strip=True)
                enlace_completo = urljoin(base_url, enlace_element['href'])
                evento_info = {
                    'titulo': titulo,
                    'resumen': resumen,
                    'enlace': enlace_completo
                }
                if borrar_primero == 0:
                    eventos_lista.append(evento_info)
            
                borrar_primero = 0 #Hacemos esto para eliminar la entrada duplicada, siempre es la primera.
    else:
        eventos_lista.append({'error': f"Error al hacer la solicitud. Código de estado: {response.status_code}"})

    return eventos_lista


def obtener_deportes():
    base_url = 'https://www.esmadrid.com/'
    url = urljoin(base_url, 'agenda-deportes-madrid')
    response = requests.get(url)
    num_eventos = 8
    mensaje = ""
    borrar_primero=1
    eventos_lista = []
    if response.status_code == 200:
        html = response.content
        soup = BeautifulSoup(html, 'html.parser')
        eventos = soup.find_all('div', class_='ds-1col')

        for evento in eventos[:num_eventos]:
            titulo_element = evento.find('h3', class_='field-name-title-field')
            resumen_element = evento.find('div', class_='field-name-resumen')
            enlace_element = evento.find('a', href=True)

            if titulo_element and resumen_element and enlace_element:
                titulo = titulo_element.get_text(strip=True)
                resumen = resumen_element.get_text(strip=True)
                enlace_completo = urljoin(base_url, enlace_element['href'])
                evento_info = {
                    'titulo': titulo,
                    'resumen': resumen,
                    'enlace': enlace_completo
                }

                if borrar_primero == 0:
                    eventos_lista.append(evento_info)
            
                borrar_primero = 0 #Hacemos esto para eliminar la entrada duplicada, siempre es la primera.
    else:
        eventos_lista.append({'error': f"Error al hacer la solicitud. Código de estado: {response.status_code}"})

    return eventos_lista


def obtener_teatro():
    url = 'https://www.atrapalo.com/entradas/madrid/teatro-y-danza/novedad/ofertas/'
    eventos_lista = []

    response = requests.get(url)

    if response.status_code == 200:
        soup = BeautifulSoup(response.text, 'html.parser')
        obras = soup.find_all('div', class_='card-result-container')

        for obra in obras[:4]:
            titulo_obra = obra.find('h2', class_='nombre').text.strip()
            if obra.find('span', class_='locality GATrackEvent_ubicacion show-for-small-only') is not None:
                localizacion = obra.find('span', class_='locality GATrackEvent_ubicacion show-for-small-only').text.strip()
            else:
                localizacion = "No disponible."
            precio = obra.find('span', class_='value').text.strip()
            descuento_container = obra.find('span', class_='status-label saving')
            descuento = descuento_container.find('span').text.strip() if descuento_container else None
            precio_descuento_container = obra.find('del', class_='hot-descuento')
            precio_descuento = precio_descuento_container.text.strip() if precio_descuento_container else None
            ahorro_container = obra.find('span', class_='status-label saving')
            ahorro = ahorro_container.find('span').text.strip() if ahorro_container else None
            enlace_obra = urljoin(url, obra.find('a', class_='img-slot')['href'])

            response_obra = requests.get(enlace_obra)
            if response_obra.status_code == 200:
                html_obra = response_obra.content
                soup_obra = BeautifulSoup(html_obra, 'html.parser')
                fechas_horas_section = soup_obra.find('section', {'aria-labelledby': 'DateBox'})

                if fechas_horas_section:
                    fecha_actual_title = fechas_horas_section.find('div', {'class': 'title'})
                    fecha_actual = fecha_actual_title.text.strip() if fecha_actual_title else 'No disponible'
                    eventos_list = fechas_horas_section.find('ol', {'class': 'event-list'})

                    if eventos_list:
                        eventos = eventos_list.find_all('li')

                        for evento in eventos:
                            hora_evento = evento.find('dd', {'class': 'time'}).text.strip()

                            evento_info = {
                                'titulo': titulo_obra,
                                'localizacion': localizacion,
                                'precio': precio,
                                'descuento': descuento,
                                'precio_descuento': precio_descuento,
                                'ahorro': ahorro,
                                'fecha': fecha_actual,
                                'hora': hora_evento,
                                'enlace_obra': enlace_obra,
                            }
                            eventos_lista.append(evento_info)
    else:
        eventos_lista.append({'error': f"Error al hacer la solicitud. Código de estado: {response.status_code}"})

    return eventos_lista


def obtener_motor():
    url = 'https://www.jarama.org/venta-de-entradas'
    response = requests.get(url)
    borrar_primero = 1
    eventos_lista = []
    if response.status_code == 200:
        html = response.content
        soup = BeautifulSoup(html, 'html.parser')

        eventos = soup.find_all('div', class_='blog-normal')

        for evento in eventos:
            fecha = evento.find('div', class_='fecha').get_text(strip=True)
            titulo = evento.find('h2', class_='post-title').get_text(strip=True)
            enlace = evento.find('a', class_='btn').get('href')

            evento_response = requests.get(enlace)
            evento_html = evento_response.content
            evento_soup = BeautifulSoup(evento_html, 'html.parser')
            precio_element = evento_soup.find('div', class_='form-group col-4 col-md-3')
            precio = precio_element.find('input', class_='form-control').get('value') if precio_element else "No disponible"

            evento_info = {
                'titulo': titulo,
                'precio': precio,
                'fecha': fecha,
                'enlace': enlace,
            }
            if borrar_primero == 0:
                    eventos_lista.append(evento_info)
            
            borrar_primero = 0 #Hacemos esto para eliminar la entrada duplicada, siempre es la primera.
    else:
        eventos_lista.append({'error': f"Error al hacer la solicitud. Código de estado: {response.status_code}"})

    return eventos_lista

def obtener_museos():
    url = 'https://museomadrid.com/actividades-culturales-en-madrid/'
    locale.setlocale(locale.LC_TIME, 'es_ES.UTF-8')

    response = requests.get(url)
    eventos_lista = []
    if response.status_code == 200:
        html = response.text
        soup = BeautifulSoup(html, 'html.parser')
        eventos = soup.find_all('div', class_='dp_pec_date_event')
        fecha_actual = datetime.now().strftime('%d/%m/%Y').lower()

        for evento in eventos:
            fecha_element = evento.find('span', class_='dp_pec_date_time')
            fecha = fecha_element.text.strip().lower() if fecha_element else 'No disponible'
            fecha = fecha.split()[1]
            if fecha == fecha_actual:
                titulo_element = evento.find('h2', class_='dp_pec_event_title')
                titulo = titulo_element.text.strip() if titulo_element else 'No disponible'
                ubicacion_element = evento.find('span', class_='dp_pec_event_location')
                ubicacion = ubicacion_element.text.strip() if ubicacion_element else 'No disponible'


                #Google search API for python. Buscamos querys relacionadas con el nombre del museo y direccion.
                link = fetch_top_search_results(f'{ubicacion}', num_results=1)
                for result in enumerate(link, 0):
                    enlace = result[1]

                evento_info = {
                    'titulo': titulo,
                    'Ubicacion': ubicacion,
                    'fecha': fecha,
                    'enlace': enlace,
                }
                eventos_lista.append(evento_info)

    else:
        eventos_lista.append({'error': f"Error al hacer la solicitud. Código de estado: {response.status_code}"})

    return eventos_lista


def obtener_restaurantes():
    user_agents = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0",
    ]
    user_agent = random.choice(user_agents)

    chrome_options = ChromeOptions()
    chrome_options.add_argument(f"user-agent={user_agent}") 
    # Use undetected_chromedriver instead of webdriver.Chrome
    driver = Chrome(options=chrome_options)
    top = 0
    mensaje = ""
    try:
        url = "https://www.thefork.es/search?cityId=328022&promotionOnly=true&timezone=Europe%2FMadrid#"
        driver.get(url)

        time.sleep(random.uniform(1, 3))

 
        page_source = driver.page_source


        soup = BeautifulSoup(page_source, 'html.parser')
        elementos_rel_noopener = soup.find_all(lambda tag: tag.name == 'a' and 'rel' in tag.attrs and tag['rel'] == ['noopener', 'noreferrer'])
        elementos_descripcion = [elemento.find_next('p', {'color': 'gray.xl'}) for elemento in elementos_rel_noopener]
        elementos_descuento = [elemento.find_next('p', {'color': 'special.red'}) for elemento in elementos_rel_noopener]
        driver.quit()

        for descripcion, descuento in islice(zip(elementos_descripcion, elementos_descuento), 10): #solo top 10 descuentos.
                            #Google search API for python. Buscamos querys relacionadas con el nombre del restaurante, direccion y palabras clave como carta y restaurante.
            top += 1

            nombre = descripcion.find_previous('h2').text.strip()
            descripcion_texto = descripcion.text.strip() 
            descripcion_texto = descripcion_texto.replace("\n", " ")
            descuento_texto = descuento.text.strip()

            link = fetch_top_search_results(f'Restaurante {nombre} en {descripcion_texto} carta', num_results=1)
            for result in enumerate(link, 0):
                enlace = result[1]

            mensaje += f'{top}#. 🍔Restaurante: {nombre}\n📍Direccion: {descripcion_texto} \n🆓Descuento: {descuento_texto} \n🔗Reservas, carta y opiniones: {enlace}\n──────────────────────────────\n'

    finally:
        top=0

    return mensaje



def obtener_fiestas():
    url = "https://www.fourvenues.com/es/discotecas-madrid"
    
    response = requests.get(url)
    eventos_lista = []
    locale.setlocale(locale.LC_TIME, 'en_EN.UTF-8')
    if response.status_code == 200:
        html = response.content
        soup = BeautifulSoup(html, 'html.parser')
        fiestas_divs = soup.find_all('div', class_='flex-grow')
        fecha_actual = datetime.now().strftime("%d/%m/%Y")
        dia_actual = datetime.now().strftime("%a")
        dias_semana_dict = {'Sun': 'Dom', 'Mon': 'Lun', 'Tue': 'Mar', 'Wed': 'Mié', 'Thu': 'Jue', 'Fri': 'Vie', 'Sat': 'Sáb'}
        dia_actual = dias_semana_dict.get(dia_actual, dia_actual) 
        fecha_actual = dia_actual + " "+ fecha_actual 
        for fiesta_div in fiestas_divs:
            fecha_element = fiesta_div.find('div', class_='subtitle badge rounded text-xs sm:text-sm bg-secondary text-white p-1 sm:px-2')
            fecha_texto = fecha_element.text.strip() if fecha_element else "No disponible"
            match = re.search(r'(\w+)\.\s(\d+)', fecha_texto)
            if match:
                dia_semana, dia = match.groups()
                dia_semana = dias_semana_dict.get(dia_semana.lower(), dia_semana)  
                fecha_formateada = f"{dia_semana} {dia}/01/2024"  
            else:
                fecha_formateada = "No disponible"
            hora_element = fiesta_div.find('div', class_='subtitle text-xs sm:text-sm')
            hora_texto = hora_element.text.strip() if hora_element else "No disponible"
            fecha_inicio = hora_texto[:5]  
            fecha_final = hora_texto[5:]  

            nombre_element = fiesta_div.find('p', class_='mt-1 sm:mt-3 font-semibold text-xl sm:text-2xl text-black dark:text-white sm:w-full sm:text-clip')
            nombre_texto = nombre_element.text.strip() if nombre_element else "No disponible"

            if fecha_actual in fecha_formateada:
                evento_info = {
                    'Nombre': nombre_texto,
                    'localizacion': nombre_texto,
                    'fecha': fecha_actual,
                    'Hora inicio': fecha_inicio,
                    'Hora final': fecha_final,
                }   
                eventos_lista.append(evento_info)
    else:
        eventos_lista.append({'error': f"Error al hacer la solicitud. Código de estado: {response.status_code}"})

    return eventos_lista


def obtener_informacion_cine(url):
    try:
        response = requests.get(url)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, 'html.parser')

        direccion = soup.select_one('.crow b:contains("Dirección:")').next_sibling.strip()
        precios = soup.select_one('.crow b:contains("Precios:")').next_sibling.strip()
        nombre_cine = soup.select_one('.std-tit').text.strip()

        informacion_cine = {
            'direccion': direccion,
            'precios': precios,
            'nombre_cine': nombre_cine,
        }
        cartelera = []
        peliculas = soup.select('.titem')
        for pelicula in peliculas:
            titulo = pelicula.select_one('.tit a')['title']
            horas = [hora.text.strip() for hora in pelicula.select('.sessions ul li span')]
            if horas is not None and horas != ' ':
                cartelera.append({
                    'titulo': titulo,
                    'horas': horas,
                })

        return informacion_cine, cartelera

    except Exception as e:
        return None, f"Error al obtener la información del cine {url}: {e}"

def obtener_cines_y_carteleras(lista_urls):
    cines_y_carteleras = []

    for url in lista_urls:
        informacion_cine, cartelera = obtener_informacion_cine(url)

        if informacion_cine is not None and cartelera:
            cine_info = {
                'informacion_cine': informacion_cine,
                'cartelera': cartelera,
            }
            cines_y_carteleras.append(cine_info)

    return cines_y_carteleras

def quiero_cartelera(update, context):
    urls_cines = [
        'https://www.ecartelera.com/cines/artistic-la-morada/',
        'https://www.ecartelera.com/cines/artistic-metropol/',
        'https://www.ecartelera.com/cines/autocine-madrid-race/',
        'https://www.ecartelera.com/cines/8,0,1.html',
        'https://www.ecartelera.com/cines/cine-arapiles/',
        'https://www.ecartelera.com/cines/515,0,1.html',
        'https://www.ecartelera.com/cines/50,0,1.html',
        'https://www.ecartelera.com/cines/613,0,1.html',
        'https://www.ecartelera.com/cines/cine-dore-filmoteca-espanola/',
        'https://www.ecartelera.com/cines/cine-embajadores-rio/',
        'https://www.ecartelera.com/cines/567,0,1.html',
        'https://www.ecartelera.com/cines/568,0,1.html',
        'https://www.ecartelera.com/cines/cines-embajadores/',
        'https://www.ecartelera.com/cines/4,0,1.html',
        'https://www.ecartelera.com/cines/20,0,1.html',
        'https://www.ecartelera.com/cines/9,0,1.html',
        'https://www.ecartelera.com/cines/570,0,1.html',
        'https://www.ecartelera.com/cines/16,0,1.html',
        'https://www.ecartelera.com/cines/53,0,1.html',
        'https://www.ecartelera.com/cines/17,0,1.html',
        'https://www.ecartelera.com/cines/571,0,1.html',
        'https://www.ecartelera.com/cines/fundacion-casa-de-mexico/',
        'https://www.ecartelera.com/cines/30,0,1.html',
        'https://www.ecartelera.com/cines/dreams-cinema-palacio-hielo/',
        'https://www.ecartelera.com/cines/35,0,1.html',
        'https://www.ecartelera.com/cines/ocine-urban-caleido/',
        'https://www.ecartelera.com/cines/38,0,1.html',
        'https://www.ecartelera.com/cines/41,0,1.html',
        'https://www.ecartelera.com/cines/44,0,1.html',
        'https://www.ecartelera.com/cines/46,0,1.html',
        'https://www.ecartelera.com/cines/sala-berlanga/',
        'https://www.ecartelera.com/cines/51,0,1.html',
        'https://www.ecartelera.com/cines/52,0,1.html',
    ]

    cines_y_carteleras = obtener_cines_y_carteleras(urls_cines)

    for cine_info in cines_y_carteleras:
        informacion_cine = cine_info['informacion_cine']
        cartelera = cine_info['cartelera']
        
        mensaje_cine = f"🎬 {informacion_cine['nombre_cine']} 🎬\n" \
                    f"📍 Dirección: {informacion_cine['direccion']}\n" \
                    f"💰 Precios: {informacion_cine['precios']}\n" \
                    f"\n🎥 Cartelera:\n"

        for pelicula in cartelera:
                
                mensaje_cine += f"\n{pelicula['titulo']}:\n"
                mensaje_cine += f"   Horarios: {', '.join(pelicula['horas'])}\n"

        update.message.reply_text(mensaje_cine)

def quiero_restaurantes(update, context):
    mensaje_restaurantes = obtener_restaurantes() 
    mensaje_personalizado = random.choice(mensajes.MENSAJES_RESTAURANTES)
    update.message.reply_text(f'{mensaje_personalizado}\n{mensaje_restaurantes}')


def saludo(update, context):
    mensaje = random.choice(mensajes.MENSAJES_HOLA)
    update.message.reply_text(mensaje)

def send_saludo(context: CallbackContext):
    saludo(context.bot, context)

def ayuda(update, context):

    mensaje_ayuda = """
    - /Hola: No mucho mas que un Hola de un robot.
    - /Ayuda: Muestra este mensaje de ayuda.
    - /QuieroCine: Encuentra información sobre el septimo arte.
    - /QuieroDeporte: Descubre eventos deportivos emocionantes.
    - /QuieroFiesta: Obtén detalles sobre las mejores fiestas y eventos nocturnos.
    - /QuieroRestaurantes: Encuentra restaurantes y lugares para comer.
    - /QuieroMuseos: Explora museos y exhibiciones culturales.
    - /QuieroMotor: Descubre eventos relacionados con el mundo del motor.
    - /QuieroEventos: Obtén información sobre eventos en general.
    - /QuieroCuriosidad: Todos los dias se aprende algo nuevo.
    - /DameUnPlan: Nada que hacer? Te doy algo aleatorio!
    ¡Espero que encuentres lo que estás buscando! 😊
    """
    mensaje_ayuda = random.choice(mensajes.MENSAJES_AYUDA) + mensaje_ayuda
    update.message.reply_text(mensaje_ayuda)

def quiero_curiosidad(update, context):
    page_title = str(wikipedia.random(pages=1))
    page_summary = wikipedia.summary(page_title, sentences=2)
    page_summary_str = page_summary.encode('utf-8').decode('utf-8')
    mensaje_curiosidad = random.choice(mensajes.MENSAJES_CURIOSIDAD)
    message = f"{mensaje_curiosidad}\n\n{page_summary_str}"

    update.message.reply_text(message)

def quiero_museos(update, context):
    eventos_lista = obtener_museos()

    if eventos_lista and 'error' not in eventos_lista[0]:
        mensaje_personalizado = random.choice(mensajes.MENSAJES_MUSEOS)
        mensaje_eventos = '\n'.join([
            f"{i + 1}.🎨 Entrada: {evento['titulo']}  \n"
            f"📅 Fecha: {evento['fecha']}  \n"
            f"📍 Ubicación: {evento['Ubicacion']}  \n"
            f"🔗 Enlace: {evento['enlace']}\n"
            f"──────────────────────────────" for i, evento in enumerate(eventos_lista)
        ]) + random.choice(mensajes.MENSAJES_ELEGIR_EVENTO)   
        opciones_teclado = [[f"{i + 1}" for i in range(len(eventos_lista))]]
        reply_markup = ReplyKeyboardMarkup(opciones_teclado, one_time_keyboard=True)
        update.message.reply_text(f'{mensaje_personalizado}\n{mensaje_eventos}', reply_markup=reply_markup)
        context.user_data["eventos_lista"] = eventos_lista

        
        return "WAITING_FOR_MUSEO_SELECTION"
    
    else:
        update.message.reply_text(random.choice(mensajes.MENSAJES_NO_EVENTOS))
        return ConversationHandler.END

def seleccionar_museo(update, context):
    try:
        opcion_seleccionada = int(update.message.text) - 1
        eventos_lista = context.user_data.get("eventos_lista")
        evento_seleccionado = eventos_lista[opcion_seleccionada]
        update.message.reply_text(
            random.choice(mensajes.MENSAJES_RESPUESTA_EVENTO) +
            f"{evento_seleccionado['titulo']}\n"
            f"{evento_seleccionado['fecha']}\n"
            f"{evento_seleccionado['Ubicacion']}\n"
        )
        cal = ics.Calendar()
        evento_ics = ics.Event()
        evento_ics.name = evento_seleccionado['titulo']
        evento_ics.description = str(f"Fecha: {evento_seleccionado['fecha']} - Ubicación: {evento_seleccionado['Ubicacion']}")
        evento_ics.begin = datetime.now() + timedelta(days=1)
        evento_ics.end = evento_ics.begin + timedelta(hours=2)
        cal.events.add(evento_ics)
        ics_filename = f"{evento_seleccionado['titulo'].replace(' ', '_')}.ics"
        with open(ics_filename, 'w') as f:
            f.writelines(cal)
            
        update.message.reply_document(open(ics_filename, 'rb'))
    except (ValueError, IndexError):
        update.message.reply_text(random.choice(mensajes.MENSAJES_NUMERO_ERRONEO))
        return "WAITING_FOR_MUSEO_SELECTION" 
    
    return ConversationHandler.END

def quiero_motor(update, context):
    eventos_lista = obtener_motor()

    if eventos_lista:
        mensaje_personalizado = random.choice(mensajes.MENSAJES_MOTOR)
        mensaje_eventos = '\n'.join([
            f"🚗 {i + 1}. {evento['titulo']} \n"
            f"💲 Precio: {evento['precio']}  \n"
            f"📅 Fecha: {evento['fecha']}  \n"
            f"🔗 Enlace: {evento['enlace']}\n"
            f"   ──────────────────────────────\n" for i, evento in enumerate(eventos_lista)
        ]) + random.choice(mensajes.MENSAJES_ELEGIR_EVENTO)

        opciones_teclado = [[f"{i + 1}" for i in range(len(eventos_lista))]]
        reply_markup = ReplyKeyboardMarkup(opciones_teclado, one_time_keyboard=True)
        update.message.reply_text(f'{mensaje_personalizado}\n{mensaje_eventos}', reply_markup=reply_markup)
        context.user_data["eventos_lista"] = eventos_lista

        return "WAITING_FOR_MOTOR_SELECTION"
    else:
        update.message.reply_text(random.choice(mensajes.MENSAJES_NO_EVENTOS))
        return ConversationHandler.END

def seleccionar_motor(update, context):
    try:
        opcion_seleccionada = int(update.message.text) - 1
        eventos_lista = context.user_data.get("eventos_lista")
        evento_seleccionado = eventos_lista[opcion_seleccionada]
        update.message.reply_text(
            random.choice(mensajes.MENSAJES_RESPUESTA_EVENTO) +
            f"{evento_seleccionado['titulo']}\n"
            f"{evento_seleccionado['precio']}\n"
            f"{evento_seleccionado['fecha']}\n"
            f"{evento_seleccionado['enlace']}\n"
        )        
        cal = ics.Calendar()
        evento_ics = ics.Event()
        evento_ics.name = evento_seleccionado['titulo']
        evento_ics.description = f"Precio: {evento_seleccionado['precio']} - Enlace: {evento_seleccionado['enlace']}"
        evento_ics.begin = datetime.now() + timedelta(days=1)
        evento_ics.end = evento_ics.begin + timedelta(hours=2)
        cal.events.add(evento_ics)

        ics_filename = f"{evento_seleccionado['titulo'].replace(' ', '_')}.ics"
        with open(ics_filename, 'w') as f:
            f.writelines(cal)

        update.message.reply_document(open(ics_filename, 'rb'))
    except (ValueError, IndexError):
        update.message.reply_text(random.choice(mensajes.MENSAJES_NUMERO_ERRONEO))
        return "WAITING_FOR_MOTOR_SELECTION" 
    
    return ConversationHandler.END


def quiero_cine(update, context):
    eventos_lista = obtener_teatro()

    if eventos_lista and 'error' not in eventos_lista[0]:
        mensaje_personalizado = random.choice(mensajes.MENSAJES_CINE)
        mensaje_eventos = '\n'.join([
            f"🎭 {i + 1}. {evento['titulo']} \n"
            f"📍 Localización: {evento['localizacion']}  \n"
            f"💲 Precio: {evento['precio']}  \n"
            f"📅 Fecha: {evento['fecha']}  \n"
            f"🕒 Hora: {evento['hora']}  \n"
            f"🔗 Compra entradas: {evento['enlace_obra']}  \n"
            f"   ──────────────────────────────\n" for i, evento in enumerate(eventos_lista)
        ]) + random.choice(mensajes.MENSAJES_ELEGIR_EVENTO)
        opciones_teclado = [[f"{i + 1}" for i in range(len(eventos_lista))]]
        reply_markup = ReplyKeyboardMarkup(opciones_teclado, one_time_keyboard=True)
        update.message.reply_text(f'{mensaje_personalizado}\n{mensaje_eventos}', reply_markup=reply_markup)
        context.user_data["eventos_lista"] = eventos_lista

        return "WAITING_FOR_CINE_SELECTION"
    else:
        update.message.reply_text(random.choice(mensajes.MENSAJES_NO_EVENTOS))
        return ConversationHandler.END

def seleccionar_cine(update, context):
    try:
        opcion_seleccionada = int(update.message.text) - 1
        eventos_lista = context.user_data.get("eventos_lista")
        evento_seleccionado = eventos_lista[opcion_seleccionada]
        update.message.reply_text(
            random.choice(mensajes.MENSAJES_RESPUESTA_EVENTO) +
            f"{evento_seleccionado['localizacion']} - "
            f"Precio: {evento_seleccionado['precio']} - "
            f"Descuento: {evento_seleccionado['descuento']} - "
            f"Precio con Descuento: {evento_seleccionado['precio_descuento']} - "
            f"Ahorro: {evento_seleccionado['ahorro']}"
        )

    
        cal = ics.Calendar()
        evento_ics = ics.Event()
        evento_ics.name = evento_seleccionado['titulo']
        evento_ics.description = str(f"{evento_seleccionado['localizacion']} - Precio: {evento_seleccionado['precio']} - Descuento: {evento_seleccionado['descuento']} - Precio sin Descuento: {evento_seleccionado['precio_descuento']} - Ahorro: {evento_seleccionado['ahorro']}")
        evento_ics.begin = datetime.now() + timedelta(days=1)
        evento_ics.end = evento_ics.begin + timedelta(hours=2)
        cal.events.add(evento_ics)

        ics_filename = f"{evento_seleccionado['titulo'].replace(' ', '_')}.ics"
        with open(ics_filename, 'w') as f:
            f.writelines(cal)

        update.message.reply_document(open(ics_filename, 'rb'))

    except (ValueError, IndexError):
        update.message.reply_text(random.choice(mensajes.MENSAJES_NUMERO_ERRONEO))
        return "WAITING_FOR_CINE_SELECTION"  
    
    return ConversationHandler.END

def quiero_deporte(update, context):
    eventos_lista = obtener_deportes()

    if eventos_lista and 'error' not in eventos_lista[0]:
        mensaje_personalizado = random.choice(mensajes.MENSAJES_DEPORTES)
        mensaje_eventos = '\n'.join([
            f"⚽ {i + 1}. {evento['titulo']} \n"
            f"📖 Resumen: {evento['resumen']}  \n"
            f"🔗 Enlace: {evento['enlace']}\n"
            f"   ──────────────────────────────\n" for i, evento in enumerate(eventos_lista)
        ]) + random.choice(mensajes.MENSAJES_ELEGIR_EVENTO)
        opciones_teclado = [[f"{i + 1}" for i in range(len(eventos_lista))]]
        reply_markup = ReplyKeyboardMarkup(opciones_teclado, one_time_keyboard=True)
        update.message.reply_text(f'{mensaje_personalizado}\n{mensaje_eventos}', reply_markup=reply_markup)
        context.user_data["eventos_lista"] = eventos_lista
        return "WAITING_FOR_DEPORTE_SELECTION"
    else:
        update.message.reply_text(random.choice(mensajes.MENSAJES_NO_EVENTOS))
        return ConversationHandler.END

def seleccionar_deporte(update, context):
    try:
        opcion_seleccionada = int(update.message.text) - 1
        eventos_lista = context.user_data.get("eventos_lista")
        evento_seleccionado = eventos_lista[opcion_seleccionada]
        update.message.reply_text(
            random.choice(mensajes.MENSAJES_RESPUESTA_EVENTO) +
            f"{evento_seleccionado['titulo']}\n"
            f"{evento_seleccionado['resumen']}\n"
            f"{evento_seleccionado['enlace']}"
        )
        
        cal = ics.Calendar()
        evento_ics = ics.Event()
        evento_ics.name = evento_seleccionado['titulo']
        evento_ics.description = str(evento_seleccionado['resumen'])
        evento_ics.begin = datetime.now() + timedelta(days=1)
        evento_ics.end = evento_ics.begin + timedelta(hours=2)
        cal.events.add(evento_ics)

        ics_filename = f"{evento_seleccionado['titulo'].replace(' ', '_')}.ics"
        with open(ics_filename, 'w') as f:
            f.writelines(cal)

        update.message.reply_document(open(ics_filename, 'rb'))
    except (ValueError, IndexError):
        update.message.reply_text(random.choice(mensajes.MENSAJES_NUMERO_ERRONEO))
    
    return ConversationHandler.END

def quiero_fiesta(update, context):
    eventos_lista = obtener_fiestas()

    if eventos_lista and 'error' not in eventos_lista[0]:
        mensaje_personalizado = random.choice(mensajes.MENSAJES_FIESTA)

        mensaje_eventos = '\n'.join([
            f"🎉 {i + 1}. Fiesta: {evento['Nombre']} \n"
            f"📅 Cuando? {evento['fecha']}  \n"
            f"🕖 Empieza? {evento['Hora inicio']}  \n"
            f"🕒 Hasta cuando? {evento['Hora final']}  \n"
            f"   ──────────────────────────────\n" for i, evento in enumerate(eventos_lista[:5])
        ]) + random.choice(mensajes.MENSAJES_ELEGIR_EVENTO)

        opciones_teclado = [[f"{i + 1}" for i in range(5)]]
        reply_markup = ReplyKeyboardMarkup(opciones_teclado, one_time_keyboard=True)
        update.message.reply_text(f'{mensaje_personalizado}\n{mensaje_eventos}', reply_markup=reply_markup)
        context.user_data["eventos_lista"] = eventos_lista
        return "WAITING_FOR_FIESTA_SELECTION"
    else:
        update.message.reply_text(random.choice(mensajes.MENSAJES_NO_EVENTOS))
        return ConversationHandler.END

def seleccionar_fiesta(update, context):
    try:
        opcion_seleccionada = int(update.message.text) - 1
        eventos_lista = context.user_data.get("eventos_lista")
        evento_seleccionado = eventos_lista[opcion_seleccionada]

        update.message.reply_text(
            random.choice(mensajes.MENSAJES_RESPUESTA_EVENTO) +
            f"{evento_seleccionado['Nombre']}\n"
            f"Cuando? {evento_seleccionado['fecha']}\n"
            f"Empieza? {evento_seleccionado['Hora inicio']}\n"
            f"Hasta cuando? {evento_seleccionado['Hora final']}\n"
        )
        
        cal = ics.Calendar()
        evento_ics = ics.Event()
        evento_ics.name = evento_seleccionado['Nombre']
        evento_ics.description = str(evento_seleccionado['Nombre'])
        evento_ics.begin = datetime.now() + timedelta(days=1)
        evento_ics.end = evento_ics.begin + timedelta(hours=2)
        cal.events.add(evento_ics)

        ics_filename = f"{evento_seleccionado['Nombre'].replace(' ', '_')}.ics"
        with open(ics_filename, 'w') as f:
            f.writelines(cal)

        update.message.reply_document(open(ics_filename, 'rb'))
    except (ValueError, IndexError):
        update.message.reply_text(random.choice(mensajes.MENSAJES_NUMERO_ERRONEO))
        return "WAITING_FOR_FIESTA_SELECTION"  
    
    return ConversationHandler.END

def quiero_eventos(update, context):
    eventos_lista = obtener_info_eventos()

    if eventos_lista and 'error' not in eventos_lista[0]:
        mensaje_personalizado = random.choice(mensajes.MENSAJES_EVENTOS)
        
        mensaje_eventos = '\n'.join([
            f"{i + 1}🎉.{evento['titulo']} \n"
            f"📖{evento['resumen']}  \n"
            f"📅{evento['enlace']}\n"
            f"   ──────────────────────────────" for i, evento in enumerate(eventos_lista)
        ])

        opciones_teclado = [[f"{i + 1}" for i in range(len(eventos_lista))]]
        reply_markup = ReplyKeyboardMarkup(opciones_teclado, one_time_keyboard=True)
        update.message.reply_text(f'{mensaje_personalizado}\n{mensaje_eventos}', reply_markup=reply_markup)
        context.user_data["eventos_lista"] = eventos_lista
        return "WAITING_FOR_EVENTO_SELECTION"
    else:
        update.message.reply_text(random.choice(mensajes.MENSAJES_NO_EVENTOS))
        return ConversationHandler.END
    

def quiero_un_plan(update, context):

    plan_aleatorio = random.randint(1, 6)

    if plan_aleatorio == 1:
        eventos_lista = obtener_info_eventos()
        evento_seleccionado = random.choice(eventos_lista)
        mensaje_personalizado = random.choice(mensajes.MENSAJES_LANZAR_EVENTO)
        mensaje_evento = (
            f"🎉 {evento_seleccionado['titulo']} \n"
            f"📅 {evento_seleccionado['resumen']}  \n"
            f"🔗 {evento_seleccionado['enlace']}\n"
        )
        update.message.reply_text(f'{mensaje_personalizado}\n{mensaje_evento}')

    elif plan_aleatorio == 2:
        eventos_lista = obtener_fiestas()
        evento_seleccionado = random.choice(eventos_lista)
        mensaje_personalizado = random.choice(mensajes.MENSAJES_LANZAR_EVENTO)
        mensaje_evento = '\n'.join([
            f"🎉 Fiesta: {evento_seleccionado['Nombre']} \n"
            f"📅 Cuando? {evento_seleccionado['fecha']}  \n"
            f"🕖 Empieza? {evento_seleccionado['Hora inicio']}  \n"
            f"🕒 Hasta cuando? {evento_seleccionado['Hora final']}  \n"

        ])
        update.message.reply_text(f'{mensaje_personalizado}\n{mensaje_evento}')
    elif plan_aleatorio == 3:
        eventos_lista = obtener_deportes()
        evento_seleccionado = random.choice(eventos_lista)
        mensaje_personalizado = random.choice(mensajes.MENSAJES_LANZAR_EVENTO)
        mensaje_evento = '\n'.join([
            f"⚽ {evento_seleccionado['titulo']} \n"
            f"📖 Resumen: {evento_seleccionado['resumen']}  \n"
            f"🔗 Enlace: {evento_seleccionado['enlace']}\n"

        ])
        update.message.reply_text(f'{mensaje_personalizado}\n{mensaje_evento}')

    elif plan_aleatorio == 4:
        eventos_lista = obtener_teatro()
        evento_seleccionado = random.choice(eventos_lista)
        mensaje_personalizado = random.choice(mensajes.MENSAJES_LANZAR_EVENTO)
        mensaje_evento = '\n'.join([
            f"🎵 {evento_seleccionado['titulo']} \n"
            f"📍 Localización: {evento_seleccionado['localizacion']}  \n"
            f"💲 Precio: {evento_seleccionado['precio']}  \n"
            f"📅 Fecha: {evento_seleccionado['fecha']}  \n"
            f"🕒 Hora: {evento_seleccionado['hora']}  \n"
            f"🔗 Compra entradas: {evento_seleccionado['enlace_obra']}  \n"
        ])
        update.message.reply_text(f'{mensaje_personalizado}\n{mensaje_evento}')
    elif plan_aleatorio == 5:
        eventos_lista = obtener_motor()
        evento_seleccionado = random.choice(eventos_lista)
        mensaje_personalizado = random.choice(mensajes.MENSAJES_LANZAR_EVENTO)
        mensaje_evento = '\n'.join([
            f"🚗 {evento_seleccionado['titulo']} \n"
            f"💲 Precio: {evento_seleccionado['precio']}  \n"
            f"📅 Fecha: {evento_seleccionado['fecha']}  \n"
            f"🔗 Enlace: {evento_seleccionado['enlace']}\n"
        ]) 
        update.message.reply_text(f'{mensaje_personalizado}\n{mensaje_evento}')
    elif plan_aleatorio == 6:
        eventos_lista = obtener_museos()
        if eventos_lista is not None:
            evento_seleccionado = random.choice(eventos_lista)
            mensaje_personalizado = random.choice(mensajes.MENSAJES_LANZAR_EVENTO)
            mensaje_evento = '\n'.join([
                f"🎨 Entrada: {evento_seleccionado['titulo']}  \n"
                f"📅 Fecha: {evento_seleccionado['fecha']}  \n"
                f"📍 Ubicación: {evento_seleccionado['Ubicacion']}  \n"
                f"🔗 Enlace: {evento_seleccionado['enlace']}\n"
            ]) 
            update.message.reply_text(f'{mensaje_personalizado}\n{mensaje_evento}')


def seleccionar_evento(update, context):
    try:
        opcion_seleccionada = int(update.message.text) - 1
        eventos_lista = context.user_data.get("eventos_lista")
        evento_seleccionado = eventos_lista[opcion_seleccionada]
        update.message.reply_text(
            random.choice(mensajes.MENSAJES_RESPUESTA_EVENTO) +
            f"{evento_seleccionado['titulo']}\n"
            f"{evento_seleccionado['resumen']}\n"
            f"{evento_seleccionado['enlace']}"
        )
        
        cal = ics.Calendar()
        evento_ics = ics.Event()
        evento_ics.name = evento_seleccionado['titulo']
        evento_ics.description = str(evento_seleccionado['resumen'] + evento_seleccionado['enlace'])
        evento_ics.begin = datetime.now() + timedelta(days=1)
        evento_ics.end = evento_ics.begin + timedelta(hours=2)
        cal.events.add(evento_ics)

        ics_filename = f"{evento_seleccionado['titulo'].replace(' ', '_')}.ics"
        with open(ics_filename, 'w') as f:
            f.writelines(cal)

        update.message.reply_document(open(ics_filename, 'rb'))


    except (ValueError, IndexError):
        update.message.reply_text(random.choice(mensajes.MENSAJES_NUMERO_ERRONEO))
        return "WAITING_FOR_EVENTO_SELECTION"  
    
    return ConversationHandler.END


#Conversation Handlers. Se establece un entrypoint a la conversacion, cuando el usuario ejecuta el comando, y un estado.

conv_handler_deporte = ConversationHandler(
    entry_points=[CommandHandler("QuieroDeporte", quiero_deporte)],
    states={
        "WAITING_FOR_DEPORTE_SELECTION": [MessageHandler(Filters.text & ~Filters.command, seleccionar_deporte)],
    },
    fallbacks=[],
)
conv_handler_fiesta = ConversationHandler(
    entry_points=[CommandHandler("QuieroFiesta", quiero_fiesta)],
    states={
        "WAITING_FOR_FIESTA_SELECTION": [MessageHandler(Filters.text & ~Filters.command, seleccionar_fiesta)],
    },
    fallbacks=[],
)

conv_handler_cine = ConversationHandler(
    entry_points=[CommandHandler("QuieroCine", quiero_cine)],
    states={
        "WAITING_FOR_CINE_SELECTION": [MessageHandler(Filters.text & ~Filters.command, seleccionar_cine)],
    },
    fallbacks=[],
)

conv_handler_motor = ConversationHandler(
    entry_points=[CommandHandler("QuieroMotor", quiero_motor)],
    states={
        "WAITING_FOR_MOTOR_SELECTION": [MessageHandler(Filters.text & ~Filters.command, seleccionar_motor)],
    },
    fallbacks=[],
)

conv_handler_museo = ConversationHandler(
    entry_points=[CommandHandler("QuieroMuseos", quiero_museos)],
    states={
        "WAITING_FOR_MUSEO_SELECTION": [MessageHandler(Filters.text & ~Filters.command, seleccionar_museo)],
    },
    fallbacks=[],
)

conv_handler_evento = ConversationHandler(
    entry_points=[CommandHandler("QuieroEventos", quiero_eventos)],
    states={
        "WAITING_FOR_EVENTO_SELECTION": [MessageHandler(Filters.text & ~Filters.command, seleccionar_evento)],
    },
    fallbacks=[],
)

def main():
    updater = Updater(TOKEN, use_context=True)
    dp = updater.dispatcher
    dp.add_handler(CommandHandler("Hola", saludo))
    dp.add_handler(CommandHandler("Ayuda", ayuda))
    dp.add_handler(conv_handler_cine)
    dp.add_handler(conv_handler_deporte)
    dp.add_handler(conv_handler_fiesta)
    dp.add_handler(CommandHandler("QuieroRestaurantes", quiero_restaurantes))
    dp.add_handler(conv_handler_museo)
    dp.add_handler(conv_handler_motor)
    dp.add_handler(conv_handler_evento)
    dp.add_handler(CommandHandler("QuieroCuriosidad", quiero_curiosidad))
    dp.add_handler(CommandHandler("QuieroCartelera", quiero_cartelera))
    dp.add_handler(CommandHandler("DameUnPlan", quiero_un_plan))




    updater.start_polling()
    updater.idle()



if __name__ == '__main__':
    main()
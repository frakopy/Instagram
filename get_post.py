import instaloader
import logging,os
import telegram
from telegram.ext import CommandHandler, Updater
from shutil import rmtree

#---------------------Configuramos loggin para saber cuando y por que paso algo-------------------------------------------------------------------------------

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s," 
)

#Creamos un obejto logger para ir informando sobre lo que va ocurriendo
logger = logging.getLogger()
#----------------------------------------------------------------------------------------------------
#Creamos los objetos necesarios para interactuar con la API de telegram:

#Creamos nuestra instancia del bot con el token que nos proporciono BotFather
bot = telegram.Bot(token='1435591794:AAGyPfhfYF8txW0GG9DYWj1nZu-Y2bl8SXw')
#Creamos la instancia de updater que estara buscando actualizaciones y las pasara a dispacher
bot_updater = Updater(bot.token)
#Creamos la instancia de dispatcher que recibira informacion de bot_updater(mensajes, comandos,etc)
dispatcher = bot_updater.dispatcher

#----------------------------Creamos nuestra instancia de instaloader------------------------------------------------------------------------
logger.info('conectando con instaloader')

#Creamos nuestra instancia especificando que no descarge comentarios, que no guarde metadas, el numero
#maximo de intentos de conexion entre otras configuraciones mas.
L = instaloader.Instaloader(download_comments=False, max_connection_attempts=9, 
                            post_metadata_txt_pattern=None, save_metadata=False, 
                            download_video_thumbnails=False, download_geotags=False, 
                            filename_pattern="{shortcode}"
                            )

logger.info('Conexión con instaloader exitosa')
#----------------------------------------------------------------------------------------------------

#----------------------------------------------------------------------------------------------------
#Creamos una lista de perfiles para los cuales deseamos descargar los posts
PERFILES = ['tucasapanama18','panafotopanama','doitcenterpanama',
            'bbbshoes','compreoalquile','bestoutletpanama','sylverlily',
            'almacenocaloca','stevenspanama','tvnpanama','minsapma'
            ]


#----------------------------------------------------------------------------------------------------

#----------------Creamos las funciones para enviar post de videos e imagenes a telegram-------------------------------------------------------------------


def post_video(post,chatid,nombre_videos):

    try:
        for nombre_video in nombre_videos:
            with open(post.owner_username+'/'+nombre_video , 'rb') as f: #leemos el video de la lista de videos
                bot.send_video(chat_id=chatid, video=f, timeout=10000) #enviamos el video al chat
        if post.caption == None: #preguntamos si el post no contiene descripcion
            bot.sendMessage(chat_id=chatid, parse_mode='HTML', text=f'<b>{post.owner_username}:</b> Este post no contiene descripción')
        else: #en caso contrario enviamos la descripcion del post
            bot.sendMessage(chat_id=chatid, parse_mode='HTML', text=f'<b>{post.owner_username}:</b> {post.caption}')                                

        #Eliminamos la carpeta que contiene todos los post previos que hayamos descargado, si no hacemos esto
        #entonces no se descargaran nuevamente por que ya existen y los post no seran mostrados en telegram,
        #ademas de que estaremos almacenando mucha informacion en nuestro disco local consumiendo memoria.
        #[rmtree(carpeta) for carpeta in PERFILES]
        rmtree(post.owner_username)

    except Exception as e:

        if 'urllib3 HTTPError' in str(e):
            mensaje = f'<b>{post.owner_username}:</b> Error al subir el video, posiblemente es muy pesado, el limite son 50MB.' 
            print(mensaje)
            bot.sendMessage(chat_id=chatid, parse_mode='HTML', text=mensaje)
            rmtree(post.owner_username)
        else:
            print('Se presento un error, volvere a intentar llamando a la funcion post_video...')
            print(e)
            post_video(post, chatid, nombre_videos)  

def post_imagen(post,chatid,nombre_imagenes):

    try:
        for nombre_imagen in nombre_imagenes:
            with open(post.owner_username+'/'+nombre_imagen , 'rb') as f:#leemos las imagen de la lista de imagenes
                bot.send_photo(chat_id=chatid, photo=f, timeout=10000) #envia la imagen al chat
        if post.caption == None:
            bot.sendMessage(chat_id=chatid, parse_mode='HTML', text=f'<b>{post.owner_username}:</b> None')
        else: #send post description
            bot.sendMessage(chat_id=chatid, parse_mode='HTML', text=f'<b>{post.owner_username}:</b> {post.caption}')                                

        #Eliminamos la carpeta que contiene todos los post previos que hayamos descargado, si no hacemos esto
        #entonces no se descargaran nuevamente por que ya existen y los post no seran mostrados en telegram,
        #ademas de que estaremos almacenando mucha informacion en nuestro disco local consumiendo memoria.
        #[rmtree(carpeta) for carpeta in PERFILES]
        rmtree(post.owner_username)

    except Exception as e:
        print('Se presento un error, volvere a intentar llamando a la funcion post_imagen...')
        print(e)
        post_imagen(post, chatid, nombre_imagenes)    
#----------------------------------------------------------------------------------------------------

def start(update,context):
    
    try:
        chatid = update.message.chat_id
        texto1 = 'Mi trabajo es recolectar los 2 primeros post de las siguientes cuentas:'
        texto2 = '\n'.join(PERFILES)
        context.bot.sendMessage(chat_id=chatid, text=texto1)
        context.bot.sendMessage(chat_id=chatid, text=texto2)
        print(chatid)
    
    except Exception as e:
        print('Se presento un error, volvere a intentar llamando a la funcion start...')
        print(e)
        start(update, context)

#-----------------creamos la funcion que obtendra los post de las cuentas---------------------------------------------------------------------------

def get_posts(update,context):

    try:

        chatid = update.message.chat_id#Obtenemos el chat id para responder
        #Enviamos un aviso para que el usuario se entere de que se estan intentando obtener los posts
        context.bot.sendMessage(chat_id=chatid, text='Intentando obtener posts por favor espere...')

        #Generamos un primer for para recorrer la lista de perfiles que hemos creado previamente
        for PERFIL in PERFILES:
            #Utilizamos esta variable para controlar cuantos posts vamos a descargar (2 en nusetro caso)
            conteo = 0

            logger.info(f'Accediendo al perfil ---> {PERFIL}')                                
            #Creamos un objeto de tipo Profile para acceder a los posts mas adelante
            perfil = instaloader.Profile.from_username(L.context, PERFIL)
            logger.info('Se accedió al perfil con éxito!!!')
            
            #Con un for recorremos todos los post del perfil que estamos iterando
            for post in perfil.get_posts():

                #incrementamos la variable conteo en 1 en cada vuelta del for para controlar la cantidad de post a descargar
                conteo +=1
                #Descargamos el post del perfil que estamos recorriendo
                download = L.download_post(post,PERFIL)
                
                carpeta_posts = post.owner_username

                #si la descarga del post ha sido exitosa entonces avisamos por pantalla con un print
                if download == True:
                    if post.is_video: #Preguntamos si el post contiene un video entonces llamamos a la funcion para postear el video
                        nombre_videos = [video for video in os.listdir(carpeta_posts) if not video.endswith('.txt')]
                        post_video(post,chatid,nombre_videos)
                    else:#De lo contrario llamamos a la funcion que posteara la imagen del post
                        nombre_imagenes = [imagen for imagen in os.listdir(carpeta_posts) if not imagen.endswith('.txt')]
                        post_imagen(post,chatid,nombre_imagenes)

                #Si nuestra varaible de control es igual a 2 significa que ya tenemos los 2 post y entonces finalizamos el segundo for
                if conteo == 2:
                    break   
            
            logger.info(f'Perfil {PERFIL} revisado!!!')                    
            
    except Exception as e:
        print('Se presento un error, volvere a intentar llamando a la funcion get_posts...')
        print(e)
        get_posts(update, context)
#----------------------------------------------------------------------------------------------------


if __name__ == "__main__":

    #Agregamos el controlador del comando post y lo asociamos a la funcion get_posts que definimos anteriormente
    dispatcher.add_handler(CommandHandler("post", get_posts))

    #Agregamos el controlador del comando start y lo asociamos a la funcion start que definimos anteriormente
    dispatcher.add_handler(CommandHandler("start", start))

    bot_updater.start_polling()
    print('\n\n')
    print('El Bot @Inta2345Bot se esta ejecutando...'.center(80).upper())
    bot_updater.idle()

    while True:
        pass







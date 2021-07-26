#!/usr/bin/env python
# pylint: disable=C0116,W0613
# This program is dedicated to the public domain under the CC0 license.

"""
First, a few callback functions are defined. Then, those functions are passed to
the Dispatcher and registered at their respective places.
Then, the bot is started and runs until we press Ctrl-C on the command line.

Usage:
Example of a bot-user conversation using ConversationHandler.
Send /start to initiate the conversation.
Press Ctrl-C on the command line or send a signal to the process to stop the
bot.
"""

import logging
from typing import Dict

from telegram import ReplyKeyboardMarkup, Update, ReplyKeyboardRemove
from telegram.ext import (
    Updater,
    CommandHandler,
    MessageHandler,
    Filters,
    ConversationHandler,
    CallbackContext,
)
from SPARQLWrapper import SPARQLWrapper, JSON

import spacy

nlp = spacy.load("en_core_web_sm")


sparql = SPARQLWrapper('http://localhost:3030/ds/sparql')

sparql2 = SPARQLWrapper('https://dbpedia.org/sparql')

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)

logger = logging.getLogger(__name__)

CHOOSING, TYPING_REPLY, TYPING_CHOICE = range(3)

reply_keyboard = [
    ['Lista de Pizzas', 'Ingredientes para armar tu pizza'],
    ['Lista de Bebidas', 'Comentarios...'],
    ['Confirmar Pedido'],
]
markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True)

def text_procesing(update, context, text):
    doc = nlp(text)
    print([(w.text, w.pos_) for w in doc])
    mytxt = update.message.text  # obtener el texto que envio el usuario
    print(mytxt)
    for w in doc:
        a = w.text, w.pos_
        update.message.reply_text(a)

def facts_to_str(user_data: Dict[str, str]) -> str:
    """Helper function for formatting the gathered user info."""
    facts = [f'{key} - {value}' for key, value in user_data.items()]
    return "\n".join(facts).join(['\n', '\n'])


def start(update: Update, context: CallbackContext) -> int:
    """Start the conversation and ask user for input."""
    update.message.reply_text(
        "Bienvenido a DcPizzaBot, para iniciar. "
        "Escoge entre los comandos para recoger tu pedido",
        reply_markup=markup,
    )

    return CHOOSING


def regular_choice(update: Update, context: CallbackContext) -> int:
    """Ask the user for info about the selected predefined choice."""
    text = update.message.text
    context.user_data['choice'] = text
    update.message.reply_text(f'{text}:')
    Ingredientes = ''
    if text == 'Lista de Pizzas':        
        sparql.setQuery('''
        PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
        PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
        PREFIX owl: <http://www.w3.org/2002/07/owl#>
        PREFIX P:<http://www.semanticweb.org/msigf65thin/ontologies/2021/5/PizzaTutorial#>
        SELECT DISTINCT ?name 
        WHERE { 
            ?s rdfs:subClassOf P:NamedPizza .
            ?s rdfs:label ?name
            FILTER (lang(?name) = 'es')
        }
        ''')
        sparql.setReturnFormat(JSON)
        qres = sparql.query().convert()
        for i in range(len(qres['results']['bindings'])):
            result = qres['results']['bindings'][i]
            name = result['name']['value']
            sparql.setQuery(f'''
                PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
                PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
                PREFIX owl: <http://www.w3.org/2002/07/owl#>
                PREFIX P:<http://www.semanticweb.org/msigf65thin/ontologies/2021/5/PizzaTutorial#>
                SELECT ?ingredients
                WHERE {{ P:{name} rdfs:subClassOf ?o .
                ?o owl:someValuesFrom ?h .
                ?h rdfs:label ?ingredients 
                FILTER (lang(?ingredients) = 'es')
                }}
            ''')
            sparql.setReturnFormat(JSON)
            qres2 = sparql.query().convert()
            for j in range(len(qres2['results']['bindings'])):
                result = qres2['results']['bindings'][j]
                ingredient = result['ingredients']['value']
                Ingredientes = Ingredientes + ingredient  + '  '
            update.message.reply_text(name + ' - ' +Ingredientes) 
            Ingredientes = ''          

        update.message.reply_text('Escribe en un mensaje la Pizza que deseas:')
    
    if text == 'Ingredientes para armar tu pizza':
        topping = ['CheeseTopping', 'MeatTopping','SeafoodTopping','PepperTopping','VegetablesTopping']
        list_length = (len(topping))
        for a in range(list_length):
            sparql.setQuery(f'''
            PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
            PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
            PREFIX owl: <http://www.w3.org/2002/07/owl#>
            PREFIX P:<http://www.semanticweb.org/msigf65thin/ontologies/2021/5/PizzaTutorial#>
            SELECT ?ingredients
            WHERE {{ ?S rdfs:subClassOf P:{topping[a]} .
            ?S rdfs:label ?ingredients 
            FILTER (lang(?ingredients) = 'es')
            }}
            ''')
            sparql.setReturnFormat(JSON)
            qres = sparql.query().convert()
            update.message.reply_text(f"Lista de {topping[a]}:")
            for i in range(len(qres['results']['bindings'])):
                result = qres['results']['bindings'][i]
                ingredients = result['ingredients']['value']
                sparql2.setQuery(f'''
                    SELECT ?res
                    WHERE {{ 
                        dbr:{ingredients} dbo:abstract ?res .
                        FILTER (lang(?res) = "es") 
                    }}
                ''')
                sparql2.setReturnFormat(JSON)
                dbpq = sparql2.query().convert()
                if len(dbpq['results']['bindings']) == 0:
                    inf = "Información no encontrada"
                else:
                    result = dbpq['results']['bindings'][0]
                    inf = result['res']['value']

                update.message.reply_text(ingredients + ': ' + inf)
        update.message.reply_text('Escribe en un mensaje los ingredientes que deseas en tu pizza:')

    if text == 'Lista de Bebidas':
        sparql.setQuery('''
        PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
        PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
        PREFIX owl: <http://www.w3.org/2002/07/owl#>
        PREFIX P:<http://www.semanticweb.org/msigf65thin/ontologies/2021/5/PizzaTutorial#>
        SELECT DISTINCT ?name 
        WHERE { 
            ?s rdfs:subClassOf P:NamedDrinks .
            ?s rdfs:label ?name
            FILTER (lang(?name) = 'es')
        }
    ''')
        sparql.setReturnFormat(JSON)
        qres = sparql.query().convert()
        for i in range(len(qres['results']['bindings'])):
            result = qres['results']['bindings'][i]
            name = result['name']['value']
            update.message.reply_text(name)

        update.message.reply_text('Escribe en un mensaje la Bebida que deseas:')

    return TYPING_REPLY


def custom_choice(update: Update, context: CallbackContext) -> int:
    """Ask the user for a description of a custom category."""
    update.message.reply_text(
        'Primero agrega un título a tu comentario, por ejemplo "Atención"'
    )

    return TYPING_CHOICE


def received_information(update: Update, context: CallbackContext) -> int:
    """Store info provided by user and ask for the next category."""
    user_data = context.user_data
    text = update.message.text
    category = user_data['choice']
    user_data[category] = text
    del user_data['choice']

    update.message.reply_text(
        "Genial, tu pedido está avanzando de esta manera:"
        f"{facts_to_str(user_data)}Puedes agregar algún comentario o cambio en tu orden en Comentarios...",
        reply_markup=markup,
    )

    return CHOOSING


def done(update: Update, context: CallbackContext) -> int:
    """Display the gathered info and end the conversation."""
    user_data = context.user_data
    if 'choice' in user_data:
        del user_data['choice']

    update.message.reply_text(
        f"Tu pedido final es: {facts_to_str(user_data)}Se lo entregaremos lo antes posible!",
        reply_markup=ReplyKeyboardRemove(),
    )

    user = update.message.from_user
    logger.info(f"Pedido de {user.first_name}: {facts_to_str(user_data)}")

    user_data.clear()
    return ConversationHandler.END


def main() -> None:
    """Run the bot."""
    # Create the Updater and pass it your bot's token.
    updater = Updater("1805941366:AAGtEq_zBYxKqnXoGxGQx966igI-rptjDP0")

    # Get the dispatcher to register handlers
    dispatcher = updater.dispatcher

    # Add conversation handler with the states CHOOSING, TYPING_CHOICE and TYPING_REPLY
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            CHOOSING: [
                MessageHandler(
                    Filters.regex('^(Lista de Pizzas|Ingredientes para armar tu pizza|Lista de Bebidas)$'), regular_choice
                ),
                MessageHandler(Filters.regex('^Comentarios...$'), custom_choice),
            ],
            TYPING_CHOICE: [
                MessageHandler(
                    Filters.text & ~(Filters.command | Filters.regex('^Confirmar Pedido$')), regular_choice
                )
            ],
            TYPING_REPLY: [
                MessageHandler(
                    Filters.text & ~(Filters.command | Filters.regex('^Confirmar Pedido$')),
                    received_information,
                )
            ],
        },
        fallbacks=[MessageHandler(Filters.regex('^Confirmar Pedido$'), done)],
    )

    #comandos dbpedia
    
    dispatcher.add_handler(conv_handler)
    

    # Start the Bot
    updater.start_polling()

    # Run the bot until you press Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT. This should be used most of the time, since
    # start_polling() is non-blocking and will stop the bot gracefully.
    updater.idle()


if __name__ == '__main__':
    main()

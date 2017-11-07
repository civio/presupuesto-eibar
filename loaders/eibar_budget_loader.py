# -*- coding: UTF-8 -*-
from budget_app.models import *
from budget_app.loaders import SimpleBudgetLoader
from decimal import *
import csv
import os
import re

class EibarBudgetLoader(SimpleBudgetLoader):

    # Parse an input line into fields
    def parse_item(self, filename, line):
        # Programme codes have changed in 2015, due to new laws. Since the application expects a code-programme
        # mapping to be constant over time, we are forced to amend budget data prior to 2015.
        # See https://github.com/dcabo/presupuestos-aragon/wiki/La-clasificaci%C3%B3n-funcional-en-las-Entidades-Locales
        # IMPORTANT: The specific regional laws apply in a different way
        programme_mapping = {
        # old programme: new programme
            '11100':'91200',    # Órganos de gobierno
            '12110':'92011',    # Secretaría general
            '12120':'92310',    # Gestión del padrón municipal de habitantes
            '12130':'92500',    # Atención a los ciudadanos
            '12140':'92020',    # Administración de personal
            '12150':'92030',    # Informática
            '12160':'92040',    # Edificios polivalentes
            '12170':'15340',    # Brigada *
            '12180':'33610',    # Ego-ibarra
            '19000':'92900',    # Imprevistos y funciones no clasificadas
            '31320':'23140',    # Apartamentos tutelados *
            '31321':'23150',    # Promoción de la igualdad de género
            '31322':'23170',    # Actuaciones contra la drogodependencia
            '31323':'23160',    # Atención a personas en situación de riesgo, desprotección, s
            '31324':'23180',    # Diversidad cultural, integración emigrantes
            '31350':'23020',    # Cooperación y ayudas el desarrollo (ONG)
            '31400':'22100',    # Otras prestaciones económicas a favor de empleados
            '32200':'24100',    # Fomento de empleo
            '32310':'32410',    # Programa cualificación profesional inicial (PCPI)
            '41320':'31170',    # Campañas de desinfección, desinsectación y desratización
            '42200':'32300',    # Funcionamiento de centros docentes *
            '43110':'15220',    # Conservación y rehabilitación de la edificación
            '43210':'15100',    # Urbanismo
            '43300':'16500',    # Alumbrado público
            '43400':'17100',    # Parques y jardines
            '43500':'13400',    # Movilidad urbana *
            '43600':'15330',    # Equipamiento urbano
            '44200':'16300',    # Limpieza viaria
            '44300':'16400',    # Cementerio
            '44500':'49300',    # Protección de consumidores y usuarios
            '44600':'44110',    # Transporte colectivo urbano de viajeros
            '45110':'33000',    # Administración general de cultura
            '45130':'33210',    # Bibliotecas públicas
            '45140':'33410',    # Unidad música
            '45151':'33422',    # Jornadas de teatro
            '45160':'33430',    # Unidad de arte
            '45180':'33330',    # Museo
            '45190':'33440',    # Unidad de imagen
            '45210':'34100',    # Fomento, promoción deportes
            '45220':'34210',    # O.A.A. Patronato municipal de instalaciones deportivas
            '45400':'33800',    # Festejos
            '45510':'33510',    # Promoción del euskara
            '45520':'33520',    # Euskaltegia
            '45610':'33720',    # Juventud
            '45620':'33710',    # Hogares de jubilados
            '53100':'45400',    # Caminos vecinales
            '53300':'17200',    # Protección y mejora del medio ambiente
            '62220':'43120',    # Mercados, abastos y lonjas
            '76010':'43310',    # Desarrollo empresarial e innovación
            '76020':'43200',    # Información y promoción turística
            '76030':'43320',    # Urb. Grade.
            # Mappings for obsolete programmes with actual multiple targets, but needed in order to mantain the timeline
            '01000':'01100',    # Deuda pública -> Deuda pública
            '22210':'132XX',    # Policía Local
            '31310':'231XX',    # Programas y servicios para personas mayores
            '31390':'231YY',    # Servicios sociales de base
            '44900':'153XX',    # Administración general bienestar comunitario
            '45150':'333XX',    # Unidad de artes escénicas. Coliseo
            '51100':'153YY',    # Obras de Infraestructura, viales y urbanización
            '61100':'930XX',    # Administración y gestión económica-financiera
        }

        # Institutional code (all income goes to the root node)
        ic_code = '000'

        # Description
        description = line[3].replace('..', '. ')
        description = description.strip()
        if not re.search('[A-Z]\.$',description):
            description = description.rstrip('.')

        # Type of data
        is_expense = (filename.find('gastos.csv')!=-1)
        is_actual = (filename.find('/ejecucion_')!=-1)

        # We got a composite identifier, with more info, so we must isolate the different bits
        full_code = line[0].strip()

        # Expenses
        if is_expense:
            # Isolate the functional code
            fc_code = full_code[14:20].replace('.', '')

            # For years before 2015 we check whether we need to amend the programme code
            year = re.search('municipio/(\d+)/', filename).group(1)
            if int(year) < 2015:
                fc_code = programme_mapping.get(fc_code, fc_code)

            # On economic codes we get the first three digits (everything but last two)
            ec_code = full_code[7:10]

            # Item numbers are the last two digits from the economic codes (fourth and fifth digit)
            item_number = full_code[11:13]

            # Parse amount
            amount = line[10 if is_actual else 5].strip()
            amount = self._parse_amount(amount)

            return {
                'is_expense': True,
                'is_actual': is_actual,
                'fc_code': fc_code,
                'ec_code': ec_code,
                'ic_code': ic_code,
                'item_number': item_number,
                'description': description,
                'amount': amount
            }

        # Income
        else:
            # On economic codes we get the first three digits (everything but last two)
            ec_code = full_code[2:5]

            # Item numbers are the last two digits from the economic codes (fourth and fifth digit)
            item_number = full_code[6:8]

            # Parse amount
            amount = line[5 if is_actual else 4].strip()
            amount = self._parse_amount(amount)

            return {
                'is_expense': False,
                'is_actual': is_actual,
                'ec_code': ec_code,
                'ic_code': ic_code,
                'item_number': item_number,
                'description': description,
                'amount': amount
            }
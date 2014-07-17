# -*- coding: utf-8 -*-
from django.db.models import get_model
from django.conf import settings
from django.http import QueryDict
from yats.shortcuts import get_ticket_model, modulePathToModuleName, touch_ticket, remember_changes, mail_ticket
from yats.forms import TicketsForm
from rpc4django import rpcmethod
#from xmlrpclib import Fault
import datetime

"""
    http://code.google.com/p/tracker-for-trac/source/browse/trunk/%40source/trac_main.pas
    http://trac-hacks.org/browser/xmlrpcplugin#0.10/tracrpc
    http://www.hossainkhan.info/content/trac-xml-rpc-api-reference
"""

APPLICATION_ERROR = -32500
FIELD_EXCLUDE_LIST = ['id', 'active_record', 'd_user', 'd_date', 'u_user', 'close_date', 'last_action_date', 'tickets_ptr']

def fieldNameToTracName(field):
    if field == 'c_date':
        return 'time created'
    if field == 'c_user':
        return 'reporter'
    if field == 'u_date':
        return 'time changed'
    if field == 'assigned':
        return 'owner'
    if field == 'caption':
        return 'summary'
    
    return field

def TracNameTofieldName(field):
    return field
    
@rpcmethod(name='system.getAPIVersion', signature=['array']) 
def getAPIVersion():
    return [1,2,3]

@rpcmethod(name='ticket.getTicketFields', signature=['array']) 
def getTicketFields(**kwargs):
    """
        array ticket.getTicketFields()
        returns an array of field items:
        [
            {
                'name': 'aaa',
                'type': 'text',
            },
            {
                'name': 'bbb',
                'type': 'textarea',
            },
            {
                'name': 'ccc',
                'type': 'select',
                'options': [
                    'a',
                    'b',
                    'c'
                ]
            },
            {
                'name': 'ddd',
                'type': 'radio',
            },            
        ]

    """
    request = kwargs['request']
    result = []
    exclude_list = FIELD_EXCLUDE_LIST
    if not request.user.is_staff:
        exclude_list = list(set(exclude_list + settings.TICKET_NON_PUBLIC_FIELDS))
        
    tickets = get_ticket_model()
    t = tickets()
    for field in t._meta.fields:
        if field.name in exclude_list:
            continue
        
        if type(field).__name__ == 'ForeignKey':
            typename = 'select'
            options = []
            opts = get_model(modulePathToModuleName(field.rel.to.__module__), field.rel.to.__name__).objects.all()
            for opt in opts:
                options.append(unicode(opt))
        else:
            # print field.__class__.__name__
            if field.__class__.__name__ == 'TextField':
                typename = 'textarea'
            else:
                typename = 'text'
                
            # TODO: bool and boolnull and choices
            options = None
        
        value = {
                'name': field.name,
                'label': fieldNameToTracName(field.name),
                'type': typename
               }
        if options:
            value['options'] = options
        result.append(value)

    return result

@rpcmethod(name='ticket.query', signature=['array'])
def query(**kwargs):
    """
    array ticket.query(string qstr="status!=closed")
    """
    request = kwargs['request']

    ids = get_ticket_model().objects.all().values_list('id', flat=True)
    return list(ids)

@rpcmethod(name='ticket.get', signature=['array', 'int'])
def get(id, **kwargs):
    """
    array ticket.get(int id)
    """
    exclude_list = FIELD_EXCLUDE_LIST
    #exclude_list.pop(exclude_list.index('id'))
    
    """
    request = kwargs['request']
    
    if not request.user.is_staff:
        exclude_list = list(set(exclude_list + settings.TICKET_NON_PUBLIC_FIELDS))
    """
    ticket = get_ticket_model().objects.get(pk=id)

    attributes = {}
    for field in ticket._meta.fields:
        if field.name in exclude_list:
            continue
        if type(field).__name__ in ['DateTimeField', 'BooleanField', 'NullBooleanField']:
            attributes[fieldNameToTracName(field.name)] = getattr(ticket, field.name)
        elif type(field).__name__ == 'DateField':
            if not getattr(ticket, field.name) == None:
                attributes[fieldNameToTracName(field.name)] = datetime.datetime.combine(getattr(ticket, field.name), datetime.datetime.min.time())
            else:
                attributes[fieldNameToTracName(field.name)] = None
            
        else:
            attributes[fieldNameToTracName(field.name)] = unicode(getattr(ticket, field.name))
    return [id, ticket.c_date, ticket.last_action_date, attributes]

@rpcmethod(name='ticket.update', signature=['array', 'int'])
def update(id, comment, attributes={}, notify=False, **kwargs):
    """
    array ticket.update(int id, string comment, struct attributes={}, boolean notify=False)
    Update a ticket, returning the new ticket in the same form as getTicket(). Requires a valid 'action' in attributes to support workflow.
    """
    request = kwargs['request']
    params = {}
    for key, value in attributes.iteritems():
        params[TracNameTofieldName(key)] = value

    ticket = get_ticket_model().objects.get(pk=id)
    
    for key, value in params.iteritems():
        setattr(ticket, key, value)
        if key == 'assigned':
            touch_ticket(value, ticket.pk)
    ticket.save(user=request.user)
    
    fakePOST = QueryDict('', mutable=True)
    fakePOST.update(params)
    
    form = TicketsForm(fakePOST, instance=ticket, is_stuff=request.user.is_staff, user=request.user, customer=request.organisation.id)
    form.cleaned_data = params
    #form.changed_data = params

    remember_changes(request, form, ticket)
            
    touch_ticket(request.user, ticket.pk)
        
    if notify:
        mail_ticket(request, ticket.pk, form)

    return get(id, **kwargs)
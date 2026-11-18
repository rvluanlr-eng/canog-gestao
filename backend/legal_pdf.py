"""Preenche somente marcadores do PDF jurídico original, preservando suas páginas.
Requer PyMuPDF. Falha quando não há espaço, sem entregar documento truncado.
"""
import io, re, fitz
from datetime import timedelta

MARKER = re.compile(r'XX-[A-Z-]+|X{3,}|05 de outubro de 2026')

def brl(cents):
    return f'{cents/100:,.2f}'.replace(',','@').replace('.',',').replace('@','.')

def date_br(value):
    return value.strftime('%d/%m/%Y') if value else ''

def make_values(c, customer, guarantor, device, details):
    if not guarantor or not details:
        raise ValueError('Fiador e dados jurídicos são obrigatórios.')
    if not c.first_due:
        raise ValueError('Primeiro vencimento obrigatório.')
    return {
        0:[customer.name,customer.cpf,customer.address,details.customer_postal_code,customer.phone,customer.email,
           guarantor.name,guarantor.cpf,guarantor.address,details.guarantor_postal_code],
        1:[device.model,device.capacity,device.color,device.imei],
        2:[str(c.installments_count),date_br(details.contract_end_date)],
        3:[brl(c.entry_cents),str(c.installments_count),brl(c.installment_cents),date_br(c.first_due)],
        6:[brl(details.activation_fee_cents) if details.activation_fee_cents is not None else ''],
        14:[f"{details.contract_date.day:02d} de {['janeiro','fevereiro','março','abril','maio','junho','julho','agosto','setembro','outubro','novembro','dezembro'][details.contract_date.month-1]} de {details.contract_date.year}" if details.contract_date else '', customer.name,customer.cpf,guarantor.name,guarantor.cpf],
        15:[date_br(details.contract_date),date_br(details.inspection_date),customer.name,customer.cpf,device.model,device.capacity,device.color,device.imei]
    }

def line_matches(page):
    found=[]
    for block in page.get_text('rawdict')['blocks']:
        if 'lines' not in block: continue
        for line in block['lines']:
            chars=[ch for span in line['spans'] for ch in span.get('chars',[])]
            string=''.join(ch['c'] for ch in chars)
            for m in MARKER.finditer(string):
                start,end=m.span()
                rect=fitz.Rect(chars[start]['bbox'])
                for ch in chars[start+1:end]: rect |= fitz.Rect(ch['bbox'])
                next_x=chars[end]['bbox'][0] if end<len(chars) else page.rect.width-48
                found.append((rect, next_x, m.group(), string))
    return found

def generate(template_bytes, c, customer, guarantor, device, details):
    values=make_values(c,customer,guarantor,device,details)
    doc=fitz.open(stream=template_bytes,filetype='pdf')
    if len(doc)!=16: raise ValueError('Modelo jurídico inesperado: esperado PDF de 16 páginas.')
    for page_no, replacements in values.items():
        page=doc[page_no]
        matches=line_matches(page)
        if len(matches)!=len(replacements):
            raise ValueError(f'Página {page_no+1}: esperados {len(replacements)} campos; encontrados {len(matches)}. Não foi alterado.')
        planned=[]
        for (rect,next_x,original,line), value in zip(matches,replacements):
            value=str(value or '').strip()
            if not value: raise ValueError(f'Página {page_no+1}: falta valor para {original}.')
            # Nunca expandir para dentro do texto jurídico seguinte.
            max_x=min(next_x-2,page.rect.width-40)
            if max_x <= rect.x0+12: raise ValueError(f'Página {page_no+1}: espaço insuficiente para {original}.')
            fontsize=min(9.5,max(5.2,rect.height*.77))
            while fontsize>=5.2 and fitz.get_text_length(value,fontname='helv',fontsize=fontsize)>max_x-rect.x0:
                fontsize-=.2
            if fontsize<5.2: raise ValueError(f'Página {page_no+1}: texto muito longo para o campo {original}; revise os dados.')
            planned.append((rect,max_x,value,fontsize))
        for rect,_,_,_ in planned:
            page.add_redact_annot(rect+(-.15,-.15,.15,.15),fill=(1,1,1))
        page.apply_redactions(images=0,graphics=0,text=0)
        for rect,max_x,value,fontsize in planned:
            # Inserção sobre a linha original, mantendo os demais elementos intactos.
            page.insert_text((rect.x0,rect.y1-1.3),value,fontname='helv',fontsize=fontsize,color=(0,0,0),overlay=True)
    # Impedir que campos genéricos passem despercebidos.
    remaining=[]
    for i,page in enumerate(doc):
        if line_matches(page): remaining.append(i+1)
    if remaining: raise ValueError(f'Campos do modelo ainda pendentes nas páginas {remaining}.')
    result=doc.tobytes(garbage=4,deflate=True)
    doc.close()
    return result

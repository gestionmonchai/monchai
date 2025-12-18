"""
Configuration des blocs pour le builder de templates
Définit les types de blocs disponibles et les templates prédéfinis
"""

# Types de blocs disponibles avec leurs propriétés par défaut
BLOCK_TYPES = {
    'logo': {
        'name': 'Logo',
        'icon': 'bi-image',
        'category': 'header',
        'default_props': {
            'size': 'M',  # S, M, L
            'alignment': 'left',  # left, center, right
            'margin_top': 0,
            'margin_bottom': 20,
        }
    },
    'title': {
        'name': 'Titre du document',
        'icon': 'bi-type-h1',
        'category': 'header',
        'default_props': {
            'text': 'DOCUMENT',
            'font_size': 28,
            'alignment': 'left',
            'bold': True,
            'italic': False,
            'color': '#8B1538',
            'margin_bottom': 10,
        }
    },
    'document_info': {
        'name': 'Infos document',
        'icon': 'bi-file-text',
        'category': 'header',
        'default_props': {
            'show_number': True,
            'show_date': True,
            'show_validity': True,
            'show_due_date': False,
            'number_label': 'N°',
            'date_label': 'Date',
            'validity_label': 'Valable jusqu\'au',
            'due_date_label': 'Échéance',
            'alignment': 'left',
            'font_size': 12,
        }
    },
    'org_info': {
        'name': 'Infos organisation',
        'icon': 'bi-building',
        'category': 'header',
        'default_props': {
            'show_name': True,
            'show_address': True,
            'show_phone': True,
            'show_email': True,
            'show_siret': True,
            'show_vat': True,
            'show_website': False,
            'alignment': 'right',
            'font_size': 11,
            'name_bold': True,
            'name_size': 16,
        }
    },
    'customer_info': {
        'name': 'Infos client',
        'icon': 'bi-person-vcard',
        'category': 'header',
        'default_props': {
            'title': 'Client :',
            'show_name': True,
            'show_address': True,
            'show_vat': True,
            'alignment': 'left',
            'font_size': 11,
            'background_color': '#f9f9f9',
            'border_left_color': '#d4af37',
            'padding': 15,
        }
    },
    'spacer': {
        'name': 'Espacement',
        'icon': 'bi-arrows-expand',
        'category': 'layout',
        'default_props': {
            'height': 30,
        }
    },
    'divider': {
        'name': 'Séparateur',
        'icon': 'bi-dash-lg',
        'category': 'layout',
        'default_props': {
            'thickness': 1,
            'color': '#ddd',
            'margin_top': 15,
            'margin_bottom': 15,
            'width': 100,  # percentage
        }
    },
    'section_title': {
        'name': 'Titre de section',
        'icon': 'bi-type-h2',
        'category': 'content',
        'default_props': {
            'text': 'Détail',
            'font_size': 14,
            'bold': True,
            'margin_top': 20,
            'margin_bottom': 10,
        }
    },
    'lines_table': {
        'name': 'Tableau des lignes',
        'icon': 'bi-table',
        'category': 'content',
        'default_props': {
            'columns': {
                'description': {'show': True, 'label': 'Désignation', 'width': 'auto'},
                'quantity': {'show': True, 'label': 'Qté', 'width': '80px'},
                'unit_price': {'show': True, 'label': 'Prix unit. HT', 'width': '120px'},
                'total': {'show': True, 'label': 'Total HT', 'width': '120px'},
                'reference': {'show': False, 'label': 'Réf.', 'width': '80px'},
                'vat_rate': {'show': False, 'label': 'TVA %', 'width': '60px'},
            },
            'font_size': 11,
            'header_bg_color': '#f5f5f5',
            'border': True,
            'striped': False,
        }
    },
    'totals': {
        'name': 'Totaux',
        'icon': 'bi-calculator',
        'category': 'content',
        'default_props': {
            'show_subtotal': True,
            'show_vat': True,
            'show_total': True,
            'subtotal_label': 'Total HT',
            'vat_label': 'TVA',
            'total_label': 'Total TTC',
            'alignment': 'right',
            'font_size': 12,
            'total_bold': True,
            'total_size': 14,
            'width': 250,
        }
    },
    'conditions': {
        'name': 'Conditions',
        'icon': 'bi-card-text',
        'category': 'content',
        'default_props': {
            'title': 'Conditions',
            'content': 'Conditions de paiement et mentions légales.',
            'show_title': True,
            'font_size': 10,
            'background_color': '#f7e7ce',
            'border_color': '#d4af37',
            'padding': 15,
            'margin_top': 30,
        }
    },
    'signature': {
        'name': 'Zone signature',
        'icon': 'bi-pen',
        'category': 'content',
        'default_props': {
            'title': 'Signature du client',
            'subtitle': 'Date et signature précédée de "Bon pour accord"',
            'height': 80,
            'show_border': True,
            'margin_top': 40,
        }
    },
    'footer': {
        'name': 'Pied de page',
        'icon': 'bi-layout-text-window-reverse',
        'category': 'footer',
        'default_props': {
            'content': '',  # Auto-filled with org info
            'show_name': True,
            'show_siret': True,
            'show_vat': True,
            'show_website': True,
            'alignment': 'center',
            'font_size': 8,
            'color': '#666',
        }
    },
    'text': {
        'name': 'Texte libre',
        'icon': 'bi-text-paragraph',
        'category': 'content',
        'default_props': {
            'content': 'Votre texte ici...',
            'font_size': 11,
            'alignment': 'left',
            'bold': False,
            'italic': False,
        }
    },
    'two_columns': {
        'name': 'Deux colonnes',
        'icon': 'bi-layout-split',
        'category': 'layout',
        'default_props': {
            'ratio': '50-50',  # 50-50, 60-40, 40-60, 70-30, 30-70
            'gap': 30,
            'left_content': [],  # Nested blocks
            'right_content': [],  # Nested blocks
        }
    },
}

# Templates prédéfinis avec blocs
BLOCK_PRESETS = {
    'quote': {
        'name': 'Devis standard',
        'description': 'Template de devis classique avec tableau des produits',
        'document_type': 'quote',
        'blocks': [
            {
                'id': 'block_1',
                'type': 'two_columns',
                'props': {
                    'ratio': '50-50',
                    'gap': 30,
                }
            },
            {
                'id': 'block_2',
                'type': 'title',
                'props': {
                    'text': 'DEVIS',
                    'font_size': 32,
                    'alignment': 'left',
                    'bold': True,
                    'color': '#8B1538',
                }
            },
            {
                'id': 'block_3',
                'type': 'document_info',
                'props': {
                    'show_number': True,
                    'show_date': True,
                    'show_validity': True,
                    'show_due_date': False,
                }
            },
            {
                'id': 'block_4',
                'type': 'org_info',
                'props': {
                    'alignment': 'right',
                    'show_siret': True,
                    'show_vat': True,
                }
            },
            {
                'id': 'block_5',
                'type': 'spacer',
                'props': {'height': 30}
            },
            {
                'id': 'block_6',
                'type': 'customer_info',
                'props': {
                    'title': 'Client :',
                    'background_color': '#f9f9f9',
                    'border_left_color': '#d4af37',
                }
            },
            {
                'id': 'block_7',
                'type': 'section_title',
                'props': {
                    'text': 'Détail du devis',
                    'margin_top': 30,
                }
            },
            {
                'id': 'block_8',
                'type': 'lines_table',
                'props': {
                    'columns': {
                        'description': {'show': True, 'label': 'Désignation'},
                        'quantity': {'show': True, 'label': 'Qté'},
                        'unit_price': {'show': True, 'label': 'Prix unit. HT'},
                        'total': {'show': True, 'label': 'Total HT'},
                    }
                }
            },
            {
                'id': 'block_9',
                'type': 'totals',
                'props': {
                    'show_subtotal': True,
                    'show_vat': True,
                    'show_total': True,
                }
            },
            {
                'id': 'block_10',
                'type': 'conditions',
                'props': {
                    'title': 'Conditions',
                    'content': 'Devis valable 30 jours.\nAcompte de 30% à la commande.\nSolde à la livraison.',
                    'background_color': '#f7e7ce',
                    'border_color': '#d4af37',
                }
            },
            {
                'id': 'block_11',
                'type': 'footer',
                'props': {
                    'show_name': True,
                    'show_siret': True,
                    'show_vat': True,
                }
            },
        ]
    },
    'invoice': {
        'name': 'Facture standard',
        'description': 'Template de facture avec mentions légales',
        'document_type': 'invoice',
        'blocks': [
            {
                'id': 'block_1',
                'type': 'title',
                'props': {
                    'text': 'FACTURE',
                    'font_size': 32,
                    'alignment': 'left',
                    'bold': True,
                    'color': '#8B1538',
                }
            },
            {
                'id': 'block_2',
                'type': 'document_info',
                'props': {
                    'show_number': True,
                    'show_date': True,
                    'show_validity': False,
                    'show_due_date': True,
                    'date_label': 'Date d\'émission',
                    'due_date_label': 'Échéance',
                }
            },
            {
                'id': 'block_3',
                'type': 'org_info',
                'props': {
                    'alignment': 'right',
                }
            },
            {
                'id': 'block_4',
                'type': 'spacer',
                'props': {'height': 30}
            },
            {
                'id': 'block_5',
                'type': 'customer_info',
                'props': {
                    'title': 'Facturé à :',
                    'background_color': '#f9f9f9',
                    'border_left_color': '#8B1538',
                }
            },
            {
                'id': 'block_6',
                'type': 'section_title',
                'props': {
                    'text': 'Détail de la facture',
                    'margin_top': 30,
                }
            },
            {
                'id': 'block_7',
                'type': 'lines_table',
                'props': {}
            },
            {
                'id': 'block_8',
                'type': 'totals',
                'props': {
                    'vat_label': 'TVA (20%)',
                    'total_bold': True,
                }
            },
            {
                'id': 'block_9',
                'type': 'conditions',
                'props': {
                    'title': 'Conditions de paiement',
                    'content': 'Paiement à 30 jours.\nEn cas de retard, pénalités de 3 fois le taux légal.\nIndemnité forfaitaire de recouvrement : 40 €.',
                    'background_color': '#fff3cd',
                    'border_color': '#856404',
                }
            },
            {
                'id': 'block_10',
                'type': 'footer',
                'props': {
                    'show_name': True,
                    'show_siret': True,
                    'show_vat': True,
                }
            },
        ]
    },
    'order': {
        'name': 'Bon de commande',
        'description': 'Template de bon de commande',
        'document_type': 'order',
        'blocks': [
            {
                'id': 'block_1',
                'type': 'title',
                'props': {
                    'text': 'BON DE COMMANDE',
                    'font_size': 28,
                    'color': '#004085',
                }
            },
            {
                'id': 'block_2',
                'type': 'document_info',
                'props': {
                    'show_validity': False,
                    'show_due_date': False,
                }
            },
            {
                'id': 'block_3',
                'type': 'org_info',
                'props': {}
            },
            {
                'id': 'block_4',
                'type': 'customer_info',
                'props': {
                    'title': 'Client :',
                    'background_color': '#e7f3ff',
                    'border_left_color': '#004085',
                }
            },
            {
                'id': 'block_5',
                'type': 'section_title',
                'props': {'text': 'Détail de la commande'}
            },
            {
                'id': 'block_6',
                'type': 'lines_table',
                'props': {}
            },
            {
                'id': 'block_7',
                'type': 'totals',
                'props': {}
            },
            {
                'id': 'block_8',
                'type': 'footer',
                'props': {}
            },
        ]
    },
    'delivery': {
        'name': 'Bon de livraison',
        'description': 'Template de bon de livraison (sans prix)',
        'document_type': 'delivery',
        'blocks': [
            {
                'id': 'block_1',
                'type': 'title',
                'props': {
                    'text': 'BON DE LIVRAISON',
                    'font_size': 28,
                    'color': '#155724',
                }
            },
            {
                'id': 'block_2',
                'type': 'document_info',
                'props': {
                    'show_validity': False,
                    'show_due_date': False,
                }
            },
            {
                'id': 'block_3',
                'type': 'org_info',
                'props': {}
            },
            {
                'id': 'block_4',
                'type': 'customer_info',
                'props': {
                    'title': 'Livré à :',
                    'background_color': '#f9f9f9',
                    'border_left_color': '#155724',
                }
            },
            {
                'id': 'block_5',
                'type': 'section_title',
                'props': {'text': 'Articles livrés'}
            },
            {
                'id': 'block_6',
                'type': 'lines_table',
                'props': {
                    'columns': {
                        'description': {'show': True, 'label': 'Désignation'},
                        'quantity': {'show': True, 'label': 'Quantité livrée'},
                        'unit_price': {'show': False},
                        'total': {'show': False},
                    }
                }
            },
            {
                'id': 'block_7',
                'type': 'signature',
                'props': {
                    'title': 'Signature du destinataire',
                    'subtitle': 'Date et signature (précédée de "Bon pour accord")',
                }
            },
            {
                'id': 'block_8',
                'type': 'footer',
                'props': {
                    'content': 'Document non contractuel - Ne constitue pas une facture',
                }
            },
        ]
    },
}


def get_block_types():
    """Retourne les types de blocs avec métadonnées pour le front"""
    return BLOCK_TYPES


def get_preset_blocks(doc_type):
    """Retourne les blocs prédéfinis pour un type de document"""
    return BLOCK_PRESETS.get(doc_type, BLOCK_PRESETS['quote'])


def get_all_presets():
    """Retourne tous les presets disponibles"""
    return BLOCK_PRESETS

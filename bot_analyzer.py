"""
Analisador do código atual do bot para identificar problemas
com detecção de tópicos duplicados
"""

import json
import os
import difflib
import re
from typing import Dict, List, Optional, Any
import unicodedata

class BotAnalyzer:
    def __init__(self):
        self.topics_file = "bot/topics.json"
        self.similarity_threshold = 0.8
    
    def load_current_topics(self) -> Optional[Dict[str, int]]:
        """Carrega os tópicos atuais do arquivo JSON"""
        try:
            if os.path.exists(self.topics_file):
                with open(self.topics_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            pass
        
        # Tenta arquivo de teste
        if os.path.exists("test_topics.json"):
            try:
                with open("test_topics.json", 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                pass
        
        return None
    
    def identify_problems(self) -> List[Dict[str, Any]]:
        """Identifica problemas na lógica atual de detecção de duplicatas"""
        problems = []
        
        # Problema 1: Normalização insuficiente
        problems.append({
            'category': 'Normalização Unicode',
            'description': 'O código atual não normaliza Unicode adequadamente, podendo falhar com emojis e caracteres especiais',
            'examples': [
                'Hagarth\'s BBW/SSBBW 🆕 vs Hagarth\'s BBW/SSBBW 🔥',
                'Café ☕ vs Cafe ☕️'
            ]
        })
        
        # Problema 2: Comparação básica
        problems.append({
            'category': 'Comparação Simples',
            'description': 'Usa apenas lowercase() simples, não detecta variações sutis',
            'examples': [
                'Group Name vs Group  Name (espaços extras)',
                'Group-Name vs Group_Name (pontuação diferente)'
            ]
        })
        
        # Problema 3: Sem fuzzy matching
        problems.append({
            'category': 'Sem Fuzzy Matching',
            'description': 'Não utiliza algoritmos de similaridade para detectar nomes parecidos',
            'examples': [
                'Hagarth BBW vs Hagarth\'s BBW',
                'Big Tits Channel vs Big Tits Group'
            ]
        })
        
        # Problema 4: Caracteres especiais
        problems.append({
            'category': 'Caracteres Especiais',
            'description': 'Não remove ou normaliza caracteres especiais adequadamente',
            'examples': [
                'Channel [VIP] vs Channel (VIP)',
                'Group • Official vs Group ● Official'
            ]
        })
        
        return problems
    
    def get_statistics(self) -> Dict[str, Any]:
        """Retorna estatísticas dos tópicos atuais"""
        topics = self.load_current_topics()
        
        if not topics:
            return {
                'total_topics': 0,
                'potential_duplicates': 0,
                'avg_similarity': 0
            }
        
        # Encontra duplicatas potenciais
        duplicates = self.find_potential_duplicates(topics)
        
        # Calcula similaridade média entre todos os pares
        similarities = []
        topic_names = list(topics.keys())
        
        for i, name1 in enumerate(topic_names):
            for name2 in topic_names[i+1:]:
                similarity = difflib.SequenceMatcher(None, name1.lower(), name2.lower()).ratio()
                similarities.append(similarity)
        
        avg_similarity = sum(similarities) / len(similarities) if similarities else 0
        
        return {
            'total_topics': len(topics),
            'potential_duplicates': len(duplicates),
            'avg_similarity': avg_similarity
        }
    
    def find_potential_duplicates(self, topics: Dict[str, int]) -> List[List[Dict[str, Any]]]:
        """Encontra grupos de tópicos potencialmente duplicados"""
        topic_names = list(topics.keys())
        duplicates = []
        processed = set()
        
        for i, name1 in enumerate(topic_names):
            if name1 in processed:
                continue
            
            group = [{'name': name1, 'similarity': 1.0}]
            
            for j, name2 in enumerate(topic_names[i+1:], i+1):
                if name2 in processed:
                    continue
                
                # Calcula similaridade
                similarity = difflib.SequenceMatcher(None, name1.lower(), name2.lower()).ratio()
                
                if similarity > self.similarity_threshold:
                    group.append({'name': name2, 'similarity': similarity})
                    processed.add(name2)
            
            if len(group) > 1:
                duplicates.append(group)
                processed.add(name1)
        
        return duplicates
    
    def create_similarity_matrix(self, topics: Dict[str, int]) -> Dict[str, Dict[str, float]]:
        """Cria matriz de similaridade entre todos os tópicos"""
        topic_names = list(topics.keys())
        matrix = {}
        
        for name1 in topic_names:
            matrix[name1] = {}
            for name2 in topic_names:
                if name1 == name2:
                    similarity = 1.0
                else:
                    similarity = difflib.SequenceMatcher(None, name1.lower(), name2.lower()).ratio()
                
                matrix[name1][name2] = round(similarity, 3)
        
        return matrix
    
    def analyze_naming_patterns(self, topics: Dict[str, int]) -> Dict[str, Any]:
        """Analisa padrões nos nomes dos tópicos"""
        patterns = {
            'has_emojis': 0,
            'has_special_chars': 0,
            'has_numbers': 0,
            'avg_length': 0,
            'common_words': {},
            'common_patterns': []
        }
        
        if not topics:
            return patterns
        
        total_length = 0
        
        for name in topics.keys():
            total_length += len(name)
            
            # Verifica emojis (caracteres Unicode não ASCII)
            if any(ord(char) > 127 for char in name):
                patterns['has_emojis'] += 1
            
            # Verifica caracteres especiais
            if re.search(r'[^\w\s]', name):
                patterns['has_special_chars'] += 1
            
            # Verifica números
            if re.search(r'\d', name):
                patterns['has_numbers'] += 1
            
            # Conta palavras comuns
            words = re.findall(r'\b\w+\b', name.lower())
            for word in words:
                patterns['common_words'][word] = patterns['common_words'].get(word, 0) + 1
        
        patterns['avg_length'] = total_length / len(topics)
        
        # Ordena palavras mais comuns
        patterns['common_words'] = dict(
            sorted(patterns['common_words'].items(), key=lambda x: x[1], reverse=True)[:10]
        )
        
        return patterns

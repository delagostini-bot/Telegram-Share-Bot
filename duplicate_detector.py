"""
Detector avançado de tópicos duplicados para o bot do Telegram
Implementa algoritmos robustos para prevenir criação de tópicos duplicados
"""

import re
import unicodedata
import difflib
from typing import Dict, Tuple, Any, Optional, List
import logging

logger = logging.getLogger(__name__)

class ImprovedDuplicateDetector:
    def __init__(self, similarity_threshold: float = 0.85):
        """
        Inicializa o detector de duplicatas
        
        Args:
            similarity_threshold: Limiar de similaridade (0.0 a 1.0)
                                Valores maiores = mais rigoroso
        """
        self.similarity_threshold = similarity_threshold
        
        # Padrões para limpeza de texto
        self.cleanup_patterns = [
            (r'[^\w\s]', ' '),           # Remove pontuação, mantém espaços
            (r'\s+', ' '),               # Normaliza espaços múltiplos
            (r'^\s+|\s+$', ''),          # Remove espaços das pontas
        ]
        
        # Palavras irrelevantes para comparação
        self.stop_words = {
            'channel', 'group', 'chat', 'oficial', 'official', 
            'vip', 'premium', 'new', 'novo', 'nova', 'the', 'a', 'an'
        }
    
    def normalize_topic_name(self, name: str) -> str:
        """
        Normaliza completamente o nome de um tópico
        
        Args:
            name: Nome original do tópico
            
        Returns:
            Nome normalizado para comparação e armazenamento
        """
        if not name:
            return ""
        
        # 1. Normalização Unicode (NFD - decomposição)
        normalized = unicodedata.normalize('NFD', name)
        
        # 2. Remove acentos mantendo caracteres base
        no_accents = ''.join(
            char for char in normalized 
            if unicodedata.category(char) != 'Mn'  # Remove marcas de combinação
        )
        
        # 3. Normalização NFC (recomposição)
        normalized = unicodedata.normalize('NFC', no_accents)
        
        # 4. Remove emojis e caracteres especiais Unicode
        # Mantém apenas letras, números, espaços e alguns símbolos básicos
        ascii_only = ''.join(
            char if ord(char) < 128 else ' '
            for char in normalized
        )
        
        # 5. Aplica padrões de limpeza
        cleaned = ascii_only
        for pattern, replacement in self.cleanup_patterns:
            cleaned = re.sub(pattern, replacement, cleaned, flags=re.IGNORECASE)
        
        # 6. Converte para minúsculas
        result = cleaned.lower().strip()
        
        logger.debug(f"Normalização: '{name}' → '{result}'")
        return result
    
    def extract_keywords(self, name: str) -> set:
        """
        Extrai palavras-chave relevantes do nome
        Remove stop words e palavras muito curtas
        """
        normalized = self.normalize_topic_name(name)
        words = set(normalized.split())
        
        # Remove stop words e palavras muito curtas
        keywords = {
            word for word in words 
            if len(word) >= 2 and word not in self.stop_words
        }
        
        return keywords
    
    def calculate_similarity(self, name1: str, name2: str) -> Tuple[float, Dict[str, Any]]:
        """
        Calcula similaridade entre dois nomes usando múltiplos algoritmos
        
        Returns:
            (similarity_score, details_dict)
        """
        if not name1 or not name2:
            return 0.0, {'method': 'empty_input', 'score': 0.0}
        
        # Normaliza ambos os nomes
        norm1 = self.normalize_topic_name(name1)
        norm2 = self.normalize_topic_name(name2)
        
        # Se são exatamente iguais após normalização
        if norm1 == norm2:
            return 1.0, {
                'method': 'exact_match',
                'score': 1.0,
                'normalized_1': norm1,
                'normalized_2': norm2
            }
        
        # Método 1: SequenceMatcher (Ratcliff-Obershelp)
        seq_similarity = difflib.SequenceMatcher(None, norm1, norm2).ratio()
        
        # Método 2: Similaridade por palavras-chave
        keywords1 = self.extract_keywords(name1)
        keywords2 = self.extract_keywords(name2)
        
        if keywords1 and keywords2:
            intersection = keywords1.intersection(keywords2)
            union = keywords1.union(keywords2)
            keyword_similarity = len(intersection) / len(union)
        else:
            keyword_similarity = 0.0
        
        # Método 3: Levenshtein aproximado usando SequenceMatcher em palavras
        words1 = norm1.split()
        words2 = norm2.split()
        
        word_similarities = []
        for w1 in words1:
            best_match = max(
                (difflib.SequenceMatcher(None, w1, w2).ratio() for w2 in words2),
                default=0.0
            )
            word_similarities.append(best_match)
        
        for w2 in words2:
            best_match = max(
                (difflib.SequenceMatcher(None, w2, w1).ratio() for w1 in words1),
                default=0.0
            )
            word_similarities.append(best_match)
        
        word_avg_similarity = sum(word_similarities) / len(word_similarities) if word_similarities else 0.0
        
        # Combina os métodos com pesos
        final_score = (
            seq_similarity * 0.4 +           # 40% - similaridade sequencial
            keyword_similarity * 0.35 +      # 35% - palavras-chave comuns  
            word_avg_similarity * 0.25       # 25% - similaridade de palavras
        )
        
        details = {
            'method': 'hybrid',
            'score': final_score,
            'normalized_1': norm1,
            'normalized_2': norm2,
            'sequence_similarity': seq_similarity,
            'keyword_similarity': keyword_similarity,
            'word_similarity': word_avg_similarity,
            'keywords_1': list(keywords1),
            'keywords_2': list(keywords2)
        }
        
        return final_score, details
    
    def are_duplicates(self, name1: str, name2: str) -> Tuple[bool, float, Dict[str, Any]]:
        """
        Verifica se dois nomes são duplicatas
        
        Returns:
            (is_duplicate, similarity_score, details)
        """
        similarity, details = self.calculate_similarity(name1, name2)
        is_duplicate = similarity >= self.similarity_threshold
        
        logger.debug(
            f"Comparação: '{name1}' vs '{name2}' "
            f"→ Similaridade: {similarity:.3f} "
            f"→ Duplicata: {is_duplicate}"
        )
        
        return is_duplicate, similarity, details
    
    def check_against_existing(self, new_name: str, existing_topics: Dict[str, int]) -> Dict[str, Any]:
        """
        Verifica se um novo nome é similar a algum tópico existente
        
        Args:
            new_name: Nome do novo tópico a verificar
            existing_topics: Dict {nome_topico: thread_id}
            
        Returns:
            Dict com resultado da verificação
        """
        if not existing_topics:
            return {
                'is_duplicate': False,
                'similar_topic': None,
                'similarity': 0.0,
                'all_scores': {}
            }
        
        best_match = None
        best_similarity = 0.0
        all_scores = {}
        
        for existing_name in existing_topics.keys():
            similarity, _ = self.calculate_similarity(new_name, existing_name)
            all_scores[existing_name] = similarity
            
            if similarity > best_similarity:
                best_similarity = similarity
                best_match = existing_name
        
        is_duplicate = best_similarity >= self.similarity_threshold
        
        result = {
            'is_duplicate': is_duplicate,
            'similar_topic': best_match if is_duplicate else None,
            'similarity': best_similarity,
            'all_scores': all_scores
        }
        
        if is_duplicate:
            logger.warning(
                f"🔴 DUPLICATA DETECTADA: '{new_name}' é similar a '{best_match}' "
                f"(Similaridade: {best_similarity:.1%})"
            )
        else:
            logger.info(
                f"✅ NOME ÚNICO: '{new_name}' não é similar a nenhum tópico existente "
                f"(Maior similaridade: {best_similarity:.1%} com '{best_match}')"
            )
        
        return result
    
    def find_duplicates_in_list(self, topics: Dict[str, int]) -> List[List[str]]:
        """
        Encontra grupos de tópicos duplicados em uma lista
        
        Returns:
            Lista de grupos, onde cada grupo é uma lista de nomes duplicados
        """
        topic_names = list(topics.keys())
        duplicate_groups = []
        processed = set()
        
        for i, name1 in enumerate(topic_names):
            if name1 in processed:
                continue
            
            group = [name1]
            
            for name2 in topic_names[i+1:]:
                if name2 in processed:
                    continue
                
                is_duplicate, _, _ = self.are_duplicates(name1, name2)
                if is_duplicate:
                    group.append(name2)
                    processed.add(name2)
            
            if len(group) > 1:
                duplicate_groups.append(group)
                processed.add(name1)
        
        return duplicate_groups

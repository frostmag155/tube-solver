import time
import random
from typing import List, Tuple, Dict, Set, Optional

class TubeSolver:
    def __init__(self, tubes: List[List[int]]):
        self.original_tubes = [tube[:] for tube in tubes]
        self.tubes = [tube[:] for tube in tubes]
        self.tube_capacity = 4
        self.moves = []
        self.visited_states = set()   
        self.total_colors = self._count_total_colors()
        self.empty_tubes_count = self._count_empty_tubes()
    
    def _count_total_colors(self) -> int:
        """Автоматически определяем количество цветов из данных"""
        all_colors = set()
        for tube in self.original_tubes:
            all_colors.update(tube)
        return len(all_colors)
    
    def _count_empty_tubes(self) -> int:
        """Считаем сколько должно быть пустых трубок"""
        return len([tube for tube in self.original_tubes if len(tube) == 0])
    
    def can_pour(self, from_index: int, to_index: int) -> bool:
        if from_index == to_index:
            return False
        if len(self.tubes[from_index]) == 0:
            return False
        if len(self.tubes[to_index]) >= self.tube_capacity:
            return False
        
        from_color = self.tubes[from_index][-1]
        to_color = self.tubes[to_index][-1] if len(self.tubes[to_index]) > 0 else None
        
        return to_color is None or to_color == from_color
    
    def pour(self, from_index: int, to_index: int) -> bool:
        if not self.can_pour(from_index, to_index):
            return False
        
        from_color = self.tubes[from_index][-1]
        
        count = 0
        for i in range(len(self.tubes[from_index]) - 1, -1, -1):
            if self.tubes[from_index][i] == from_color:
                count += 1
            else:
                break
        
        space = self.tube_capacity - len(self.tubes[to_index])
        pour_count = min(count, space)
        
        poured = self.tubes[from_index][-pour_count:]
        self.tubes[from_index] = self.tubes[from_index][:-pour_count]
        self.tubes[to_index].extend(poured)
        
        self.moves.append((from_index, to_index))
        return True
    
    def get_state_hash(self) -> str:
        return '|'.join(sorted(','.join(map(str, tube)) for tube in self.tubes))
    
    def is_solved(self) -> bool:
        completed = 0
        empty = 0
        
        for tube in self.tubes:
            if len(tube) == 0:
                empty += 1
                continue
            if len(tube) != self.tube_capacity:
                return False
            color = tube[0]
            for i in range(1, len(tube)):
                if tube[i] != color:
                    return False
            completed += 1
        
        return completed == self.total_colors and empty == self.empty_tubes_count
    
    def get_empty_tubes(self) -> List[int]:
        return [i for i, tube in enumerate(self.tubes) if len(tube) == 0]
    
    def get_tubes_with_space(self) -> List[int]:
        return [i for i, tube in enumerate(self.tubes) if len(tube) < self.tube_capacity]
    
    def analyze_colors(self) -> Dict:
        color_analysis = {}
        
        all_colors = set()
        for tube in self.tubes:
            all_colors.update(tube)
        
        for color in all_colors:
            positions = []
            total_count = 0
            
            for tube_index, tube in enumerate(self.tubes):
                for pos, tube_color in enumerate(tube):
                    if tube_color == color:
                        total_count += 1
                        positions.append({
                            'tube_index': tube_index,
                            'position': pos,
                            'depth': len(tube) - pos - 1,
                            'is_top': pos == len(tube) - 1
                        })
            
            if total_count == self.tube_capacity:
                positions.sort(key=lambda x: x['depth'], reverse=True)
                
                color_analysis[color] = {
                    'total_count': total_count,
                    'positions': positions,
                    'is_collectible': any(p['is_top'] for p in positions),
                    'max_depth': max(p['depth'] for p in positions) if positions else 0
                }
        
        return color_analysis
    
    def find_target_color(self) -> Optional[int]:
        analysis = self.analyze_colors()
        best_color = None
        best_score = -1
        
        for color, data in analysis.items():
            if not data['is_collectible']:
                continue
            
            score = data['max_depth'] * 10
            
            top_positions = [p for p in data['positions'] if p['is_top']]
            if len(top_positions) > 1:
                score += len(top_positions) * 5
            
            if score > best_score:
                best_score = score
                best_color = color
        
        return best_color
    
    def find_moves_for_color(self, target_color: int) -> List[Dict]:
        moves = []
        empty_tubes = self.get_empty_tubes()
        tubes_with_space = self.get_tubes_with_space()
        
        target_positions = []
        for tube_index, tube in enumerate(self.tubes):
            for pos, tube_color in enumerate(tube):
                if tube_color == target_color:
                    target_positions.append({
                        'tube_index': tube_index,
                        'position': pos,
                        'depth': len(tube) - pos - 1,
                        'is_top': pos == len(tube) - 1,
                        'blocking_colors': tube[pos + 1:]
                    })
        
        target_positions.sort(key=lambda x: x['depth'], reverse=True)
        
        for pos in target_positions:
            if pos['is_top']:
                from_idx = pos['tube_index']
                
                for to_idx in tubes_with_space:
                    if from_idx != to_idx and self.can_pour(from_idx, to_idx):
                        moves.append({
                            'from': from_idx,
                            'to': to_idx,
                            'type': 'collect',
                            'priority': 80,
                            'description': f'Сбор цвета {target_color} из {from_idx} в {to_idx}'
                        })
            else:
                blocking_tube = pos['tube_index']
                blocking_colors = pos['blocking_colors']
                
                if blocking_colors:
                    for to_idx in tubes_with_space:
                        if blocking_tube != to_idx and self.can_pour(blocking_tube, to_idx):
                            moves.append({
                                'from': blocking_tube,
                                'to': to_idx,
                                'type': 'free',
                                'priority': 90,
                                'description': f'Освобождение цвета {target_color} из {blocking_tube}'
                            })
                    
                    for empty_tube in empty_tubes:
                        if blocking_tube != empty_tube and self.can_pour(blocking_tube, empty_tube):
                            moves.append({
                                'from': blocking_tube,
                                'to': empty_tube,
                                'type': 'free_to_empty',
                                'priority': 95,
                                'description': f'Использование пустой пробирки для освобождения цвета {target_color}'
                            })
        
        tubes_with_target_top = []
        for i, tube in enumerate(self.tubes):
            if tube and tube[-1] == target_color:
                tubes_with_target_top.append(i)
        
        if len(tubes_with_target_top) > 1:
            for i in range(len(tubes_with_target_top)):
                for j in range(i + 1, len(tubes_with_target_top)):
                    from_idx = tubes_with_target_top[i]
                    to_idx = tubes_with_target_top[j]
                    
                    if self.can_pour(from_idx, to_idx):
                        moves.append({
                            'from': from_idx,
                            'to': to_idx,
                            'type': 'merge',
                            'priority': 70,
                            'description': f'Объединение цвета {target_color} из {from_idx} и {to_idx}'
                        })
        
        return sorted(moves, key=lambda x: x['priority'], reverse=True)
    
    def find_backup_move(self) -> Optional[Dict]:
        for to_idx, tube in enumerate(self.tubes):
            if len(tube) == self.tube_capacity - 1:  
                color = tube[0]
                if all(c == color for c in tube):
                    for from_idx in range(len(self.tubes)):
                        if (from_idx != to_idx and 
                            self.can_pour(from_idx, to_idx) and 
                            self.tubes[from_idx] and 
                            self.tubes[from_idx][-1] == color):
                            return {'from': from_idx, 'to': to_idx}
        
        for from_idx in range(len(self.tubes)):
            for to_idx in range(len(self.tubes)):
                if self.can_pour(from_idx, to_idx):
                    return {'from': from_idx, 'to': to_idx}
        
        return None
    
    def solve(self) -> bool:
        self.tubes = [tube[:] for tube in self.original_tubes]
        self.moves = []
        self.visited_states.clear()
        
        move_count = 0
        
        print(f"Начинаем решение: {self.total_colors} цветов, {self.empty_tubes_count} пустых трубок")
        
        while not self.is_solved():
            state_hash = self.get_state_hash()
            
            if state_hash in self.visited_states:
                all_moves = []
                for from_idx in range(len(self.tubes)):
                    for to_idx in range(len(self.tubes)):
                        if self.can_pour(from_idx, to_idx):
                            all_moves.append((from_idx, to_idx))
                
                if all_moves:
                    random_move = random.choice(all_moves)
                    self.pour(random_move[0], random_move[1])
                else:
                    break
            else:
                self.visited_states.add(state_hash)
                
                target_color = self.find_target_color()
                
                if target_color:
                    color_moves = self.find_moves_for_color(target_color)
                    
                    if color_moves:
                        best_move = color_moves[0]
                        self.pour(best_move['from'], best_move['to'])
                    else:
                        backup_move = self.find_backup_move()
                        if backup_move:
                            self.pour(backup_move['from'], backup_move['to'])
                        else:
                            break
                else:
                    backup_move = self.find_backup_move()
                    if backup_move:
                        self.pour(backup_move['from'], backup_move['to'])
                    else:
                        break
            
            move_count += 1
            
            if move_count % 100 == 0:
                completed = sum(1 for tube in self.tubes 
                               if len(tube) == self.tube_capacity and len(set(tube)) == 1)
                empty = len(self.get_empty_tubes())
                print(f"Ход {move_count}: завершено {completed}/{self.total_colors}, пустых: {empty}/{self.empty_tubes_count}")
        
        return self.is_solved()
    
    def print_solution(self):
        print(f"\nПоследовательность ходов ({len(self.moves)} ходов):")
        for i, move in enumerate(self.moves):
            if i % 10 == 0 and i > 0:
                print()
            print(f"({move[0]}, {move[1]})", end=" ")
        
        print("\n\nФинальное состояние:")
        for i, tube in enumerate(self.tubes):
            if len(tube) == 0:
                status = "ПУСТАЯ"
            elif len(tube) == self.tube_capacity and len(set(tube)) == 1:
                status = "ЗАВЕРШЕНА"
            else:
                status = "СМЕШАННАЯ"
            print(f"{i}: {tube} - {status}")
        
        completed = sum(1 for tube in self.tubes 
                       if len(tube) == self.tube_capacity and len(set(tube)) == 1)
        empty = len(self.get_empty_tubes())
        print(f"\nЗавершено: {completed}/{self.total_colors}, Пустых: {empty}/{self.empty_tubes_count}")
        print(f"Всего ходов: {len(self.moves)}")


if __name__ == "__main__":
    
    tubes_12_colors = [
        [1, 8, 12, 4],    [6, 3, 9, 7],     [11, 2, 5, 10],   
        [7, 1, 4, 12],    [9, 6, 10, 3],    [2, 5, 8, 11],    
        [12, 7, 3, 1],    [4, 9, 6, 10],    [5, 11, 2, 8],    
        [10, 4, 1, 7],    [8, 3, 12, 6],    [11, 9, 5, 2],    
        [],[],               []               
    ]

    tubes = tubes_12_colors 
    
    solver = TubeSolver(tubes)
    
    start_time = time.time()
    solved = solver.solve()
    end_time = time.time()
    
    if solved:
        print(f"\n Решено за {len(solver.moves)} ходов!")
    else:
        print(f"\n Не решено за {len(solver.moves)} ходов")
    print(f"Время выполнения: {(end_time - start_time):.2f} секунд")
    
    solver.print_solution()
from typing import List


def calculate_bi(fractals: List[dict]) -> List[dict]:
    # Combine tops and bottoms into a single list of fractals, ordered by index
    # fractals = tops + bottoms
    # fractals.sort(key=lambda x: x['index'])

    # Step 2: Process fractals to remove unnecessary ones
    i = 0
    while i < len(fractals) - 1:
        current = fractals[i]
        next_fractal = fractals[i + 1]
        if current['type'] == next_fractal['type']:
            if current['type'] == 'top':
                if current['high'] < next_fractal['high']:
                    # Discard current, keep next
                    fractals.pop(i)
                else:
                    i += 1
            elif current['type'] == 'bottom':
                if current['low'] > next_fractal['low']:
                    # Discard current, keep next
                    fractals.pop(i)
                else:
                    i += 1
        else:
            i += 1

    # Step 3: Form Bi from the processed fractals
    cleaned_fractals = []
    i = 0
    while i < len(fractals):
        start_fractal = fractals[i]
        start_type = start_fractal['type']
        j = i + 1
        while j < len(fractals) and fractals[j]['type'] == start_type:
            j += 1
        cleaned_fractals.append(start_fractal)
        i = j

    # Now, form Bi from cleaned_fractals
    bi_list = []
    for i in range(len(cleaned_fractals) - 1):
        fractal1 = cleaned_fractals[i]
        fractal2 = cleaned_fractals[i + 1]
        # Check if there is at least one K-line between the fractals
        if fractal2['index'] - fractal1['index'] < 4:
            continue  # Not enough K-lines between fractals
        # Check if the high and low satisfy the conditions
        if fractal1['type'] == 'top' and fractal2['type'] == 'bottom':
            if fractal1['high'] <= fractal2['low']:
                continue  # High of top not higher than low of bottom
        elif fractal1['type'] == 'bottom' and fractal2['type'] == 'top':
            if fractal2['high'] <= fractal1['low']:
                continue  # High of top not higher than low of bottom
        else:
            continue  # Should not happen
        # Form Bi
        bi = {
            'start_index': fractal1['index'],
            'end_index': fractal2['index'],
            'start_type': fractal1['type'],
            'end_type': fractal2['type'],
            'start_high': fractal1['high'],
            'start_low': fractal1['low'],
            'end_high': fractal2['high'],
            'end_low': fractal2['low']
        }
        bi_list.append(bi)

    return bi_list

# Example usage:
top_bottoms = [
    {'type': 'top', 'index': 0, 'high': 5645, 'low': 5581},
    {'type': 'bottom', 'index': 2, 'high': 5577, 'low': 5568},
    {'type': 'top', 'index': 3, 'high': 5579, 'low': 5574},
    {'type': 'bottom', 'index': 4, 'high': 5570, 'low': 5562},
    {'type': 'top', 'index': 10, 'high': 5602, 'low': 5595},
    {'type': 'bottom', 'index': 11, 'high': 5593, 'low': 5589},
    {'type': 'top', 'index': 12, 'high': 5607, 'low': 5601},
    {'type': 'bottom', 'index': 13, 'high': 5594, 'low': 5588}
]

bi_list = calculate_bi(top_bottoms)
for bi in bi_list:
    print(bi)

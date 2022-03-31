import csv
import random
import sys

def read_header(row):
    fields = row.split()
    header = []
    begin = 0
    for field in fields:
        end = row.index(field, begin) + len(field)
        header.append({'column_name': field, 'begin': begin, 'end': end})
        begin = end

    return header

def cast_percent(val):
    return float(val[:-1]) / 100.0

def cast_null(val):
    return None

def cast_field(summary, field, cast):
    summary[field] = cast(summary[field])

def read_summary(row, header):
    fields = [field['column_name'] for field in header]
    values = [row[field['begin']: field['end']].strip() for field in header]
    # print(values, file=sys.stderr)
    summary = dict(zip(fields, values))
    cast_field(summary, 'approx_unique', int)
    cast_field(summary, 'count', int)
    cast_field(summary, 'null_percentage', cast_percent)

    field_type = summary['column_type']
    if field_type == 'BIGINT':
        cast_field(summary, 'min', int)
        cast_field(summary, 'max', int)
        cast_field(summary, 'avg', float)
    elif field_type == 'DOUBLE':
        cast_field(summary, 'min', float)
        cast_field(summary, 'max', float)
        cast_field(summary, 'avg', float)
    else:
        cast_field(summary, 'avg', cast_null)

    return summary

def read_summaries(infile):
    schema = {}
    header = None
    for line in infile:
        row = line[:-1]
        if header:
            summary = read_summary(row, header)
            column_name = summary['column_name']
            schema[column_name] = summary
        else:
            header = read_header(row)
            # print(header, file=sys.stderr)

    return schema

class Generator():
    def __init__(self, summary):
        print(summary, file=sys.stderr)
        self._summary = summary
        self._domain = set()
        self._choices = None

        # Bounds for all domains
        self._name = self._summary['column_name']
        self._min = self._summary['min']
        self._max = self._summary['max']

        #   Enforce the known values
        self._required = []
        if self._summary['null_percentage'] > 0:
            self._required.append(None)
        self._required.append(self._min)
        if self._min != self._max:
            self._required.append(self._max)

    def generate_value(self):
        return None

    def generate(self):
        # If we have the full domain, choose an existing value
        if len(self._domain) >= self._summary['approx_unique']:
            if not self._choices:
                self._choices = tuple([value for value in self._domain])
            return random.choice(self._choices)

        # Prioritise the required values
        if len(self._domain) < len(self._required):
            val = self._required[len(self._domain)]

        # Randomly choose a NULL
        elif random.random() < self._summary['null_percentage']:
            val = None

        # Or a real value
        else:
            val = self.generate_value()

        self._domain.add(val)
        return val

class GenerateFloat(Generator):
    def __init__(self, summary):
        super().__init__(summary)

        self._mu = self._summary['avg']
        self._sigma = min(self._max - self._mu, self._mu - self._min) / 5.0
        #print(self._name, self._mu, self._sigma, file=sys.stderr)

    def generate_value(self):
        return max(min(random.gauss(self._mu, self._sigma), self._max), self._min)

class GenerateInt(GenerateFloat):
    def generate_value(self):
        return int(round(super().generate_value()))

class GenerateString(Generator):
    def generate_value(self):
        return self._min

generator_factory = {
    'BIGINT': GenerateInt,
    'DOUBLE': GenerateFloat,
    'VARCHAR': GenerateString,
    'NULL': Generator,
}

def generate_row(generators):
    return {field: generators[field].generate() for field in generators.keys()}

def main():
    schema = read_summaries(sys.stdin)
    #print(schema, file=sys.stderr)

    fieldnames = tuple(schema.keys())
    writer = csv.DictWriter(sys.stdout, fieldnames=fieldnames)
    writer.writeheader()

    types = {field: schema[field]['column_type'] for field in fieldnames}
    generators = {field: generator_factory[types[field]](schema[field]) for field in fieldnames}
    nrows = schema[fieldnames[0]]['count']
    dots = max(nrows // 100, 100)
    nrows = 10
    for r in range(0,nrows):
        writer.writerow(generate_row(generators))
        if 0 == r % dots:
            sys.stderr.write('.')
            sys.stderr.flush()
    sys.stderr.write('\n')
    sys.stderr.flush()

if __name__ == "__main__":
    main()

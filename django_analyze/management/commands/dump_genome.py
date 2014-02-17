import re
import sys

import django
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db.models import Q
from django.core import serializers

from optparse import make_option

from django_analyze import models

class Command(BaseCommand):
    args = '<genome id>'
    help = 'Efficiently exports the given genome to JSON.'
    option_list = BaseCommand.option_list + (
#        make_option('--force', action='store_true', default=False),
#        make_option('--delete-existing', action='store_true', default=False),
    )

    def handle(self, genome_id, **options):
        genome_id = int(genome_id)
        
        def to_json_str(obj):
            json_str = serializers.serialize('json', [obj],
#                use_natural_foreign_keys=True,
#                use_natural_primary_keys=True,
                use_natural_keys=True,
                indent=4,
            )
            json_str = re.sub('"pk":\s+[0-9]+', '"pk": null', json_str, re.DOTALL|re.I)
            json_str = json_str.strip()[1:-1].strip()
            return json_str
        
        q0 = models.Genome.objects.filter(id=genome_id)
        
        # Genes.
        q1 = models.Gene.objects.filter(genome__id=genome_id)
        
        # Species.
        q2 = models.Species.objects.filter(genome__id=genome_id)
        
        # Genotypes.
        q3 = models.Genotype.objects.filter(genome__id=genome_id)
        
        # Genotype gene values.
        q4 = models.GenotypeGene.objects.filter(genotype__genome__id=genome_id)
        
        queries = [q0, q1, q2, q3, q4]
        total = sum([_q.count() for _q in queries])
        i = 0
        print '[\n'
        for q in queries:
            for obj in q.iterator():
                i += 1
                if not i % 10:
                    print>>sys.stderr, '\r%i of %i (%.02f%%)' % (i, total, float(i)/total*100),
                    sys.stderr.flush()
                first = i == 1
                last = i == total
                json_str = to_json_str(obj)
                if not last:
                    json_str = json_str+','
                print json_str
        print ']'
        print>>sys.stderr, '\r%i of %i' % (i, total),
        print>>sys.stderr, '\nDone!'
        sys.stderr.flush()
        
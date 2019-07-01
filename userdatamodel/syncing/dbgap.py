class dbGapSyncer(object):
    def read_file(self, filepath):
        p = Popen(
            ["crypt", self.dbgap_key],
            stdin=open(filepath, "r"),
            stdout=PIPE,
            stderr=open(os.devnull, "w"),
        )

        return StringIO(p.communicate()[0])

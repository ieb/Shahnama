class Hijri:

    short_form = ["","muh","saf","ra1","ra2","ju1","ju2","raj","shb","ram","shw","dhk","dhh"]
    
    long_form = ["","Muharram","Safar","Rabi' I","Rabi' II","Jumada I","Jumada II",
                 "Rajab","Sha'ban","Ramadan","Shawwal","Dhu'l-Qa'da","Dhu'l-Hijja"]
    
    short_to_number = {}
    
    for (i,x) in enumerate(short_form):
        short_to_number[x] = i
        
    def __init__(self):
        pass

    def _blank_to_none(self,s):
        if s is None or s.strip(' -') == '':
            return None
        return s

    def _blank_to_none_num(self,s):
        s = self._blank_to_none(s)
        if s is None:
            return None
        try:
            return str(int(s))
        except:
            return None

    def _convert_month_in(self,s):
        s = self._blank_to_none(s)
        if s is None:
            return None
        try:
            return Hijri.short_to_number[s.lower()]
        except:
            raise Exception("Bad Hijri date "+s)            

    def _from_parts(self,y,m,d): # month is 1-based
        self._y = y
        self._m = m
        self._d = d

    def _from_string(self,s):
        if s is None or s.strip() == '':
            self._from_parts(None,None,None)
        else:
            parts = s.split("/")
            while len(parts) < 3:
                parts.append(None)
            self._from_parts(self._blank_to_none_num(parts[0]),
                             self._convert_month_in(parts[1]),
                             self._blank_to_none_num(parts[2]))

    def _num_to_short_blank(self,value,len):
        if value is None:
            return '-' * len
        return ("%%0%dd" % len) % int(value)

    def _num_to_blank(self,value):
        if value is None:
            return ''
        return "%d" % int(value)

    def _month_to_short(self,value,len):
        if value is None:
            return '-' * len
        val = Hijri.short_form[int(value)]
        return val[0].upper() + val[1:]

    def _month_to_long(self,value):
        if value is None:
            return ''
        val = Hijri.long_form[int(value)]
        return val[0].upper() + val[1:]

    def to_string(self):
        return "%s/%s/%s" % (self._num_to_short_blank(self._y,4),
                             self._month_to_short(self._m,3),
                             self._num_to_short_blank(self._d,2))

    def to_long_string(self):
        if self._y is None and self._m is None and self._d is None:
            return "unspecified"
        return "%s %s %s" % (self._num_to_blank(self._d),
                             self._month_to_long(self._m),
                             self._num_to_blank(self._y))
        
    def __str__(self):
        return "%s/%s/%s" % (self._y,self._m,self._d)

    @staticmethod    
    def from_string(s): # Can raise exception if a bad date
        out = Hijri()
        out._from_string(s)
        return out
    
    @staticmethod    
    def date(d):
        return Hijri.from_string(d).to_long_string()


if __name__ == '__main__':
    h = Hijri.from_string('1021/Ram/08')
    print h.to_string()
    print h.to_long_string()
    h = Hijri.from_string('----/---/--')
    print h.to_string()
    print h.to_long_string()

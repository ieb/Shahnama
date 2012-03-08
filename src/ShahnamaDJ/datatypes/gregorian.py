import re

re_century = re.compile(r"^([0-9][0-9]?)(st|nd|rd|th)$")
re_year = re.compile(r"^[0-9]+$")

class Gregorian:

    short_form = ["","jan","feb","mar","apr","may","jun","jul","aug","sep","oct","nov","dec"]
    long_form = ["","January","February","March","April","May","June","July","August","September","October","November","December"]
    
    short_to_number = {}
    
    for (i,x) in enumerate(short_form):
        short_to_number[x] = i
    
    uncertainties = {
        'h1': 'first half',
        'h2': 'second half',
        'ea': 'early',
        'mi': 'middle',
        'la': 'late',
        'q1': 'first quarter',
        'q2': 'second quarter',
        'q3': 'third quarter',
        'q4': 'fourth quarter',
        '-1': 'or previous century',
        '+1': 'or next century',
        'ca': 'circa'
    }

    uncertainties_year = {
        '-1': 'or previous year',
        '+1': 'or next year',
        'ca': 'circa'
    }

    uncertainties_month = {
        '-1': 'or previous month',
        '+1': 'or next month',
        'ca': 'circa'
    }

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
            return Gregorian.short_to_number[s.lower()]
        except:
            raise Exception("Bad Gregorian month "+s)

    def _month_to_long(self,value):
        if value is None:
            return ''
        val = Gregorian.long_form[int(value)]
        return val[0].upper() + val[1:] + " "
    
    def _num_to_blank(self,value,add_blank = True,th = False):
        if value is None:
            return ''
        value = int(value)
        if th:
            value = Gregorian._th(value)
        return "%s%s" % (value,' ' if add_blank else '')

    def _from_parts(self,s,y,m,d): # month is 1-based, s is specifier (as a string)
        self._y = y
        self._m = m
        self._d = d
        self._s = s.lower() if s is not None else None
    
    def _from_string(self,s):
        if s is None or s.strip() == '':
            self._from_parts(None,None,None,None)            
            return
        parts = s.split('/')
        if re_year.match(parts[0].strip()) and ( len(parts) == 1 or parts[1].strip() == '' ):
            self._from_parts('y',parts[0].strip(),None,None)
            return
        if len(parts) < 2:
            raise Exception('Bad Gregorian date '+s) 
        parts[1] = parts[1].lower()
        if parts[1][0] == 'c':
            # Format xxyy/Czz, where x is a number, y is a positional abbrev., z is an uncertainty (may be missing)
            if parts[1] != 'c' and not parts[1][1:] in Gregorian.uncertainties:
                raise Exception("Bad gregorian date "+s)
            self._from_parts(parts[1],parts[0][0:2],None,None)
        elif parts[1][0:2] == 'hc' and len(parts) >= 4:
            # Format xxxx/Hcz/mmm/ddd, where x is a number, z is y,m,d, m is month (short form), d is day
            # means date derived from Hijri year/month/day
            if not parts[1][2] in ('y','m','d'):
                raise Exception("Bad gregorian date "+s)
            self._from_parts(parts[1],parts[0],self._convert_month_in(parts[2]),self._blank_to_none_num(parts[3]))
        elif parts[1][0] == 'y' and len(parts) >= 4:
            # Format xxxx/Yss/mm/dd, where x is a year, s is an uncertainty or end year, m is a month and d is a day
            if parts[1][1:] in Gregorian.uncertainties_year:
                self._from_parts(parts[1],parts[0],self._convert_month_in(parts[2]),self._blank_to_none_num(parts[3]))
            else:
                try:
                    self._from_parts(parts[1],parts[0],self._convert_month_in(parts[2]),self._blank_to_none_num(parts[3]))
                except:
                    raise Exception("Bad gregorian date "+s)
        elif parts[1][0] == 'm' and len(parts) >= 4:
            # Format xxxx/Mss/mm/dd, where x is a year, s is an uncertainty or end year, m is a month and d is a day
            if parts[1][1:] in Gregorian.uncertainties_month:
                self._from_parts(parts[1],parts[0],self._convert_month_in(parts[2]),self._blank_to_none_num(parts[3]))
            else:
                try:
                    self._from_parts(parts[1],parts[0],self._convert_month_in(parts[2]),self._blank_to_none_num(parts[3]))
                except:
                    raise Exception("Bad gregorian date "+s)
        elif parts[1].strip().strip('-') == '' and len(parts) >= 4:
            year = parts[0]
            m = re_century.match(year)
            if m:
                self._from_parts('c',m.group(1),None,None)
            else:            
                self._from_parts('',parts[0],self._convert_month_in(parts[2]),self._blank_to_none_num(parts[3]))            
        else:
            raise Exception("Bad gregorian date "+s)            

    def to_long_string(self):
        if self._s is None:
            return "unspecified"
        elif self._s == '':
            return "%s%s%s" % (self._num_to_blank(self._d,th = True),self._month_to_long(self._m),self._num_to_blank(self._y,False))
        elif self._s[0] == 'c':
            if self._s == 'c':
                return "%s century" % Gregorian._th(self._y)
            else:
                return "%s century, %s" % (Gregorian._th(self._y),Gregorian.uncertainties[self._s[1:]])
        elif self._s[0:2] == 'hc':
            return "%s%s%s, converted from nearest Hijri %s" % (self._num_to_blank(self._d,th = True),
                                                                self._month_to_long(self._m),
                                                                self._num_to_blank(self._y,False),
                                                                {'d': 'day','m': 'month','y': 'year'}[self._s[2]])
        elif self._s[0] == 'y':
            if self._s[1:] in Gregorian.uncertainties_year:
                return "%s, %s" % (self._y,Gregorian.uncertainties_year[self._s[1:]])
            else:
                return "%s, to %s" % (self._y,self._s[1:])
        elif self._s[0] == 'm':
            if self._s[1:] in Gregorian.uncertainties_month:
                return "%s %s, %s" % (self._month_to_long(self._m),self._y,Gregorian.uncertainties_month[self._s[1:]])
            else:
                return "%s %s, to %s" % (self._month_to_long(self._m),self._y,self._s[1:])

    def order(self):
        if self._s is None:
            return (1,None,None,None)
        elif self._s == '':
            return (0,self._y,self._m if self._m else 99,self._d if self._d else 99)
        elif self._s[0] == 'c':
            return (0,self._y*100,99,99)
        elif self._s[0:2] == 'hc':
            return (0,self._y,self._m if self._m else 99,self._d if self._d else 99)
        elif self._s[0] == 'y':
            return (0,self._y,self._m if self._m else 99,self._d if self._d else 99)
        elif self._s[0] == 'm':
            return (0,self._y,self._m if self._m else 99,self._d if self._d else 99)
        return (2,None,None,None)
        
    @staticmethod
    def _th(x):
        try:
            x = int(x)
            s = "th"
            if (x%100 < 9 or x%100 > 20) and x%10 < 4:
                s = ['th','st','nd','rd'][x%10]
            return "%d%s" % (x,s)
        except:
            return x
    
    @staticmethod
    def from_string(s):
        out = Gregorian()
        out._from_string(s)
        return out
    
    @staticmethod
    def date(d):
        return Gregorian.from_string(d).to_long_string()

if __name__ == '__main__':
    g = Gregorian.from_string('')
    print g.to_long_string()
    g = Gregorian.from_string('17th/Ch2')
    print g.to_long_string()
    g = Gregorian.from_string('17th/C')
    print g.to_long_string()
    g = Gregorian.from_string('1341/Hcd/May/14')
    print g.to_long_string()
    g = Gregorian.from_string('1824/Hcm/Mar/--')
    print g.to_long_string()
    g = Gregorian.from_string('1829/Hcy/---/--')
    print g.to_long_string()
    g = Gregorian.from_string('1610/Yca/---/--')
    print g.to_long_string()
    g = Gregorian.from_string('1590/Y1600/---/--')
    print g.to_long_string()
    g = Gregorian.from_string('1846/M+1/Jul/--')
    print g.to_long_string()
    g = Gregorian.from_string('1602/---/---/--')
    print g.to_long_string()
    g = Gregorian.from_string('1602/---/Mar/--')
    print g.to_long_string()
    g = Gregorian.from_string('1602/---/Mar/01')
    print g.to_long_string()

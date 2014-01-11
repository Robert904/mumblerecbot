cimport cpython

cpdef sound_add(s1, s2):
    cdef unsigned int cpt = 0
    cdef unsigned int size = len(s1)
    
    cdef char *s1_chr = s1
    cdef short *s1_int = <short *>s1_chr
    cdef char *s2_chr = s2
    cdef short *s2_int = <short *>s2_chr

    result = "\x00" * len(s1)
    cdef char *result_chr = result
    cdef short *result_int = <short *>result_chr
    
    while cpt < size/2:
        if s1_int[cpt] > 0 and s2_int[cpt] > 0:
            result_int[cpt] = ( s1_int[cpt] + s2_int[cpt] ) - (( s1_int[cpt] * s2_int[cpt] ) / 32767 ) 
        elif s1_int[cpt] < 0 and s2_int[cpt] < 0:
            result_int[cpt] = - (( -s1_int[cpt] - s2_int[cpt] ) - (( s1_int[cpt] * s2_int[cpt] ) / 32767 ))
        else:
            result_int[cpt] = s1_int[cpt] + s2_int[cpt]

        cpt += 1
        
    return result
    	


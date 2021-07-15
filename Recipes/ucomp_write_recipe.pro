pro ucomp_write_recipe,wave_region, step, nwave, nsum, nbeam, mode, expose

;  procedure to write a recipe, called by make_recipe widget


debug='yes'			;debug mode, 'yes' or 'no'
tab=string(9B)


;  specify central wavelength depending on region

wave0 = float(wave_region)


;  compute wavelengths

waves = (indgen(nwave)-fix(nwave/2))*step +wave0
if debug eq 'yes' then print,waves


;  create background mode sequence

print,mode
case mode of
	'BOTH': back_mode = ['BOTH']
	'BLUE': back_mode = ['BLUE']
  'RED': back_mode = ['RED']
  'ALL': back_mode = ['BOTH','BLUE','RED']
endcase
nmode = n_elements(back_mode)

if debug eq 'yes' then print,nmode


;  compute expected execution time

ntot = nwave*nbeam*nmode
extime = expose*ntot*4*nsum/1000. + 0.25*ntot


;  create filename and write file

name = strcompress(string(format='(i4.0,"_",i2.2,"_",i1,"beam_",a,".rcp")', $
 fix(wave0),nwave,nbeam,mode),/remove_all)
if debug eq 'yes' then print,name

openw,1,name


;  write out recipe

;   modulate polarization fastest, then beam, then wavelength
;	alternate increasing and decreasing order of wavelength

beams = ['RCAM','TCAM']

printf,1,"DATE  ",systime()
printf,1
printf,1,format='("#Expected execution time:",f7.3," s")',extime
printf,1
printf,1,"#DATATYPE BEAM  WAVELENGTH  NUMSUMS"

for imode=0,nmode-1 do begin
  for ibeam=0,nbeam-1 do begin
    for iwave=0,nwave-1 do begin
    	printf,1, format='("DATA",a,a,a,a,a,f7.2,a,i1)', $
        tab,beams[ibeam],tab,back_mode[imode],tab,waves[iwave],tab,nsum
    endfor
    printf,1
  endfor
endfor

close,1
end
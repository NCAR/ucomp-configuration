pro make_recipe_event, ev

common recipe, wave_region, step, nwave, nsum, nbeam, nrep, mode, expose, ext_id, num_id,step_id

dir='C:\Users\tomczyk\Documents\GitHub\ucomp-configuration\Recipes'
cd,dir

;  the 9 wavelength regions observed by the ucomp

;regions=['530.3','637.4','656.3','691.8','706.2','789.4','1074.7', '1079.8', '1083.0']       ;original UCoMP regions
regions=['637.4','670.2','706.2','761.1','789.4','802.4','991.3','1074.7','1079.8' ]          ;updated UCoMP regions

default_step = [0.05,0.05,0.05,0.06,0.07,0.07,0.09,0.11,0.11]         ;corresponding default step size
back_mode = ['BOTH', 'BLUE', 'RED','ALL']

debug='yes'			;debug mode, 'yes' or 'no'

widget_control, ev.id, get_uvalue=value
if (n_elements(value) eq 0) then value = ''
if debug eq 'yes' then print,value

case (value) of				;  if done, close widget
	"DONE": begin
		WIDGET_CONTROL, /destroy, ev.top
  		return
	end

 	"Write": begin
		if debug eq 'yes' then print,wave_region, step, nwave, nsum, nbeam, mode, expose, nrep
  		ucomp_write_recipe,wave_region, step, nwave, nsum, nbeam, mode, expose, nrep
 	end

 	"NWave": begin
 		nwave=ev.value
  		if debug eq 'yes' then print,nwave,' wavelengths'
  	end

 	"Expose": begin
 		expose=ev.value
  		if debug eq 'yes' then print,expose,' (ms) exposure'
  	end

	"NBeam": begin
		nbeam=ev.value
		if debug eq 'yes' then print,nbeam,' beams'
	end

	"NRep": begin
	  nrep=ev.value
	  if debug eq 'yes' then print,nrep,' repetitions'
	end

	"NSum": begin
		nsum=ev.value
		if debug eq 'yes' then print,nsum,' sums'
	end

	"Mode": begin
		mode = back_mode[ev.index]
  		if debug eq 'yes' then print,mode
  	end

	"Region": begin
		wave_region = regions[ev.index]
		step = default_step[ev.index]
		widget_control, step_id, set_value=string(format='(f5.3)',step)
  		if debug eq 'yes' then print,wave_region
  	end

  else:
  endcase

;  compute and display number of images in recipe
;  compute and display estimated recipe execution time in seconds (assume 0.25 s lcvr delay)

if mode eq 'ALL' then nmode=3 else nmode=1
ntot = nwave*nbeam*nrep*nmode
extime = expose*ntot*4*nsum/1000. + 0.25*ntot

widget_control, num_id, set_value=string(format='(i3)',ntot)

widget_control, ext_id, set_value=string(format='(f6.1)',extime)
print,'test'
end

;-------------------------------------------------------------------------------------------------------------------------------------------

pro ucomp_make_recipe

common recipe, wave_region, step, nwave, nsum, nbeam, nrep, mode, expose, ext_id, num_id,step_id

;	set default values

wave_region = '1074.7'
step = 0.11
nwave = 5l
nsum = 16l
nbeam = 2l
nrep = 4
mode = 'BOTH'
nmode = 1l
expose = 80l

;  compute default recipe execution time

ntot = nwave*nbeam*nrep*nmode
extime = expose*ntot*4*nsum/1000. + 0.25*ntot

swin = !d.window	;Previous window

base = WIDGET_BASE(title='make_recipe', /row)
WIDGET_CONTROL, /MANAGED, base

b1 = WIDGET_BASE(base, /frame, /column)
t1 = WIDGET_TEXT(b1, xsize=80, ysize=20, /SCROLL, $
value = [ 'UCoMP Recipe Generating Application', $
'', $
'    This routine generates scripts to obtain data with the Upgraded Coronal Multi-Channel', $
'    Polarimeter (UCoMP) instrument. These scripts, also known as recipes, define the ', $
'    wavelength, output beam, background mode and number of sums for a sequence of ', $
'    observations. Each line of a recipe represents a group of image data at the specified ', $
'    wavelength, in all 4 modulation states, and for both cameras that will be saved in a', $ 
'    single fits file. A recipe typically consists of a number commands in a single wavelength', $ 
'    region, and takes from 30 to 100 seconds. The observing code executes a list of recipes,', $
'    listed in a cookbook (.cbk) file, during the day.' ])

WIDGET_CONTROL, base, set_uvalue=t1

b2 = WIDGET_BASE(base, /frame, /column, space=30)

t1 = widget_base(b1, /row)

;  create widget to display number of images in recipe

t2 = widget_label(t1, value = 'Number of Commands in Recipe:')
num_id = widget_text(t1, /editable, xsize=10, ysize=1,value=string(format='(i3)',ntot))

;  create widget to display recipe execution time

t2 = widget_label(t1, value = 'Recipe Execution Time (seconds):')
ext_id = widget_text(t1, /editable, xsize=10, ysize=1,value=string(format='(f6.1)',extime))

;  create push button for Done

t1 = widget_button(b2, value="Done", uvalue = "DONE")

;  create push button for write recipe

t1 = widget_button(b2, value="Write Recipe", uvalue = "Write")

;  create droplist for wavelength region

regions = ['637.4','670.2','706.2','761.1','789.4','802.4','991.3','1074.7','1079.8']
t2 = widget_droplist(b2,title='Wavelength Region',uvalue='Region', $
 value = regions)

;  create droplist for background mode

back_mode = ['BOTH', 'BLUE', 'RED','ALL']
t2 = widget_droplist(b2,title='Background Mode',uvalue='Mode', $
 value=back_mode)

;  create slider for number of wavelengths

t1 = widget_slider(b2, title='Number of Wavelengths (make odd)',uvalue='NWave',value=5, $
 minimum=1, maximum=21)

;  create slider for wavelength step size

t1 = widget_label(b2, value = 'Wavelength Step (nm):')
step_id = widget_text(b2, /editable, xsize=6, ysize=1,value=string(format='(f5.3)',step))

;  create slider for exposure time

t1 = widget_slider(b2, title='Exposure Time (ms)',uvalue='Expose',value=80, $
 minimum=1, maximum=81)

;  create slider for number of sums

t1 = widget_slider(b2, title='Number of Sums',uvalue='NSum',value=16, $
 minimum=1, maximum=20)

;  create slider for number of beams

t1 = widget_slider(b2, title='Number of Beams',uvalue='NBeam',value=2, $
 minimum=1, maximum=2)

 ;  create slider for number of repetitions

 t1 = widget_slider(b2, title='Number of Repetitions',uvalue='NRep',value=2, $
   minimum=1, maximum=10)

widget_control, base, /realize
XMANAGER, 'make_recipe', base, /NO_BLOCK

end

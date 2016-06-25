import utils
import os
import shutil

# Run Spades
def spades(spades_folder, threads, fastq_files, notUseCareful, maxMemory, minCoverage):
	contigs = os.path.join(spades_folder, 'contigs.fasta')

	command = ['spades.py', '', '--only-assembler', '--threads', str(threads), '--memory', str(maxMemory), '--cov-cutoff', str(minCoverage), '-1', fastq_files[0], '-2', fastq_files[1], '-o', spades_folder]

	if not notUseCareful:
		command[1] = '--careful'

	run_successfully, stdout, stderr = utils.runCommandPopenCommunicate(command)

	return run_successfully, contigs

# Rename contigs and contigs.fasta file while filtering for contigs length
def renameFilterContigs(sampleName, outdir, spadesContigs, minContigsLength):
	newContigsFile = os.path.join(outdir, str(sampleName + '.contigs.fasta'))
	number_contigs = 0
	number_bases = 0

	writer = open(newContigsFile, 'wt')
	contigHeader = ""
	contigSequence = ""
	contigs = open(spadesContigs)
	for line in contigs:
		if line[0] == '>':
			if contigHeader != "":
				if len(contigSequence) >= minContigsLength:
					writer.write(contigHeader + "\n")
					writer.write(contigSequence + "\n")
					number_bases = number_bases + len(contigSequence)
					number_contigs = number_contigs + 1
			contigHeader = ""
			contigSequence = ""
			contigHeader = ">" + sampleName + "_" + line[1:].splitlines()[0]
		else:
			contigSequence = contigSequence + line.splitlines()[0]
	if len(contigSequence) >= minContigsLength:
		writer.write(contigHeader + "\n")
		writer.write(contigSequence + "\n")
		number_bases = number_bases + len(contigSequence)
		number_contigs = number_contigs + 1
	writer.close()

	return newContigsFile, number_contigs, number_bases

# Run SPAdes procedure
def runSpades(sampleName, outdir, threads, fastq_files, notUseCareful, maxMemory, minCoverage, minContigsLength, estimatedGenomeSizeMb):
	pass_qc = False
	failing = {}
	failing['sample'] = False

	contigs = None

	# Create SPAdes output directory
	spades_folder = os.path.join(outdir, 'spades', '')
	utils.removeDirectory(spades_folder)
	os.mkdir(spades_folder)

	run_successfully, contigs = spades(spades_folder, threads, fastq_files, notUseCareful, maxMemory, minCoverage)

	if run_successfully:
		print 'Filtering for contigs with at least ' + str(minContigsLength) + ' nucleotides'
		contigsFiltered, number_contigs, number_bases = renameFilterContigs(sampleName, outdir, contigs, minContigsLength)
		print str(number_bases) + ' assembled nucleotides in ' + str(number_contigs) + ' contigs'

		if number_bases >= estimatedGenomeSizeMb*1000000*0.5 and number_bases <= estimatedGenomeSizeMb*1000000*1.5:
			if number_contigs <= 100*number_bases/1500000:
				pass_qc = True
			else:
				failing['sample'] = 'The number of assembled contigs (' + str(number_contigs) + ') exceeds ' + str(100*number_bases/1500000)
				print failing['sample']
		else:
			failing['sample'] = 'The number of assembled nucleotides (' + str(number_bases) + ') are lower than 50\% or higher than 150\% of the provided estimated genome size'
			print failing['sample']
	else:
		failing['sample'] = 'Did not run'
		print failing['sample']

	utils.removeDirectory(spades_folder)

	return run_successfully, pass_qc, failing, contigsFiltered
"""
    Tasca 5 : So estèreo i fitxers WAVE 

    Nom i cognoms: Bernat Rubiol
"""

import struct


def readWave(fitWave):
    '''
    Lectura del fitxer fitWave
    '''
    with open(fitWave, "rb") as fpWave:
        capcelera = '<4sI4s'
        chunkID, chunkSize, formato = struct.unpack(capcelera, fpWave.read(struct.calcsize(capcelera)))
        if chunkID != b'RIFF' or formato != b'WAVE':
            raise Exception('El fitxer no té format WAVE')

        fmtCap = '<4sI2H2I2H'
        (subChunk1ID, subChunk1Size, audioFormat, numChannels,
         sampleRate, byteRate, blockAlign, bitsPerSample) = struct.unpack(fmtCap, fpWave.read(struct.calcsize(fmtCap)))

        fmtData = '<4sI'
        subChunk2ID, subChunk2Size = struct.unpack(fmtData, fpWave.read(struct.calcsize(fmtData)))
        data = fpWave.read(subChunk2Size)

        bytesPerSample = bitsPerSample // 8
        fmtSample = 'h' if bytesPerSample == 2 else 'i'

        numSamples = subChunk2Size // (bytesPerSample * numChannels)
        fmtSen = '<' + str(numSamples * numChannels) + fmtSample
        samples = struct.unpack(fmtSen, data)

        if numChannels == 1:
            senyal = [samples]
        elif numChannels == 2:
            senyal = [samples[::2], samples[1::2]]

    return senyal, sampleRate


def writeWave(fileWave, signal, sampleRate, bitsPerSample=16):
    '''
    Escriptura del fitxer
    '''
    bytesPerSample = bitsPerSample // 8
    numChannels = len(signal)
    numSamples = len(signal[0])
    blockAlign = numChannels * bytesPerSample
    byteRate = sampleRate * blockAlign
    subChunk2Size = numSamples * blockAlign
    chunkSize = 36 + subChunk2Size

    with open(fileWave, 'wb') as fpWave:
        # RIFF + WAVE
        fpWave.write(struct.pack('<4sI4s', b'RIFF', chunkSize, b'WAVE'))

        # fmt subchunk
        fpWave.write(struct.pack('<4sI2H2I2H',
            b'fmt ', 16, 1, numChannels, sampleRate, byteRate, blockAlign, bitsPerSample))

        # data subchunk
        fpWave.write(struct.pack('<4sI', b'data', subChunk2Size))

        # samples
        fmtSample = 'h' if bytesPerSample == 2 else 'i'
        fmtSen = '<' + str(numSamples * numChannels) + fmtSample

        if numChannels == 1:
            data = signal[0]
        else:
            # Interleaving
            data = [None] * (numSamples * numChannels)
            for i in range(numSamples):
                data[i * 2] = signal[0][i]
                data[i * 2 + 1] = signal[1][i]

        fpWave.write(struct.pack(fmtSen, *data))


def estereo2mono(ficEste, ficMono, canal=2):
    '''
    Converteix un fitxer estèreo a mono segons el canal:
    0: esquerre, 1: dret, 2: semisuma, 3: semidiferència
    '''
    signal, sampleRate = readWave(ficEste)

    if canal == 0:
        writeWave(ficMono, [signal[0]], sampleRate)
    elif canal == 1:
        writeWave(ficMono, [signal[1]], sampleRate)
    elif canal == 2:
        semisuma = [(l + r) // 2 for l, r in zip(signal[0], signal[1])]
        writeWave(ficMono, [semisuma], sampleRate)
    elif canal == 3:
        semidiferencia = [(l - r) // 2 for l, r in zip(signal[0], signal[1])]
        writeWave(ficMono, [semidiferencia], sampleRate)


def mono2estereo(ficIzq, ficDer, ficEste):
    '''
    Combina dos fitxers mono en un fitxer estèreo
    '''
    signalIzq, sampleRate = readWave(ficIzq)
    signalDer, _ = readWave(ficDer)
    writeWave(ficEste, [signalIzq[0], signalDer[0]], sampleRate)


def codEstereo(ficEste, ficCod):
    '''
    Codifica un senyal estèreo en format 32 bits mono amb semisuma i semidiferència
    '''
    signal, sampleRate = readWave(ficEste)

    semisuma = [(l + r) // 2 for l, r in zip(signal[0], signal[1])]
    semidiferencia = [(l - r) // 2 for l, r in zip(signal[0], signal[1])]
    
    # Combina semisuma (16 bits més significatius) i semidiferència (16 bits menys)
    codificat = [(s << 16) | (d & 0xFFFF) for s, d in zip(semisuma, semidiferencia)]
    writeWave(ficCod, [codificat], sampleRate, bitsPerSample=32)


def decEstereo(ficCod, ficEste):
    '''
    Decodifica un fitxer mono de 32 bits (semisuma+semidiferència) a estèreo
    '''
    signal, sampleRate = readWave(ficCod)
    codificat = signal[0]

    semisuma = [(x >> 16) for x in codificat]
    semidiferencia = [((x & 0xFFFF) ^ 0x8000) - 0x8000 for x in codificat]  # Sign-extend

    esquerre = [s + d for s, d in zip(semisuma, semidiferencia)]
    dret = [s - d for s, d in zip(semisuma, semidiferencia)]

    writeWave(ficEste, [esquerre, dret], sampleRate)


signal, sampleRate = readWave('wav/komm.wav')
estereo2mono("wav/komm.wav", "dreta.wav", 1)

% Escena 1 - MATLAB
% Es necesario tener los frames generados por el script de Python para ejecutar este código. Carpeta: 'datos/'
% Generar una nueva secuencia de salida en 'salidas/' para cada ejecución. Deben tener el sufijo '_salida'.
% También en 'salidas/' se guardará un video con la secuencia de frames procesados, con el mismo sufijo '_salida'.


%% ============================================================
%%  ARCHIVO: escena1mat.m
%%  Escena 1 – Objetos BLANCOS, cámara en órbita 90°
%%  Detección: invertir imagen → umbralización Otsu → regionprops
%%  Clasifica figuras 2D por circularidad y relación de aspecto
%% ============================================================
clear; clc; close all;

dir_datos  = fullfile('datos',   'escena1');
dir_salida = fullfile('salidas', 'escena1');
if ~exist(dir_salida,'dir'), mkdir(dir_salida); end

secs = {'escena1_1','escena1_2','escena1_3'};

for e = 1:numel(secs)
    nom  = secs{e};
    din  = fullfile(dir_datos,  nom);
    dout = fullfile(dir_salida, [nom '_salida']);
    if ~exist(dout,'dir'), mkdir(dout); end

    arch = dir(fullfile(din,'*.png'));
    if isempty(arch), fprintf('Sin imágenes en %s\n', din); continue; end

    vid = VideoWriter(fullfile(dir_salida, [nom '_salida.mp4']), 'MPEG-4');
    vid.FrameRate = 1; open(vid);

    for k = 1:numel(arch)
        img  = imread(fullfile(din, arch(k).name));
        gris = rgb2gray(img);

        % El suelo blanco bien iluminado es casi 255.
        % Al invertir, las sombras y caras oscuras de objetos quedan
        % con valores altos → fáciles de umbralizar.
        inv = imcomplement(gris);
        T   = max(graythresh(inv), 0.06);  % mínimo para escenas muy planas
        bw  = imbinarize(inv, T);
        bw  = imopen(bw,  strel('disk', 3));  % quita ruido
        bw  = imclose(bw, strel('disk', 8));  % cierra huecos
        bw  = imfill(bw,  'holes');
        bw  = bwareaopen(bw, 400);            % elimina regiones pequeñas

        st = regionprops(bw, 'Centroid','BoundingBox','Area','Perimeter');
        io = img; nd = 0;

        for i = 1:numel(st)
            A = st(i).Area; if A < 400, continue; end
            nd = nd + 1;
            cx = st(i).Centroid(1);  cy = st(i).Centroid(2);
            bb = st(i).BoundingBox;  P  = max(st(i).Perimeter, 1);

            circ = 4*pi*A / P^2;          % 1 = círculo perfecto
            asp  = bb(3) / max(bb(4), 1); % w/h bounding box

            if     circ > 0.72,           et = 'Cilindro'; c = 'green';
            elseif asp  > 1.4 || asp < 0.70, et = 'Prisma';   c = 'blue';
            else,                          et = 'Cubo';     c = 'red';
            end

            io = insertShape(io,  'Rectangle', bb, 'Color',c, 'LineWidth',2);
            io = insertMarker(io, [cx cy],      '+', 'Color',c, 'Size',15);
            io = insertText(io,   [cx-30 cy-22], et, 'FontSize',11, ...
                'TextColor',c, 'BoxColor','white', 'BoxOpacity',0.65);
        end

        io = insertText(io, [5 5], sprintf('F%d/%d | Det:%d', k, numel(arch), nd), ...
            'FontSize',12,'TextColor','black','BoxColor','white','BoxOpacity',0.8);
        imwrite(io, fullfile(dout, arch(k).name));
        writeVideo(vid, io);
    end
    close(vid);
    fprintf('✓ %s_salida generada\n', nom);
end
fprintf('=== Escena 1 completa ===\n');